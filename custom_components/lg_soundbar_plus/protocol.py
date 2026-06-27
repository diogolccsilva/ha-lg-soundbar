"""Local control client for LG soundbars (TCP port 9741).

The wire protocol (AES-256-CBC with a fixed key/IV and a ``0x10`` + 4-byte
big-endian length frame) is derived from the Apache-2.0 licensed
``google/python-temescal`` project (https://github.com/google/python-temescal).

This is a self-contained re-implementation that fixes a few issues in the
original which matter for a long-running Home Assistant integration:

* reads each frame fully (the original used a single ``recv`` and silently
  dropped multi-segment frames such as ``SETTING_VIEW_INFO`` — exactly the one
  carrying the speaker levels we care about),
* reconnects with exponential backoff instead of a tight loop, and
* exposes a generic ``set`` so *any* documented key can be written (the
  original lacks setters for side/rear-side/rear-top/dialog levels and the EQ
  tone controls, and its night-mode setter writes the wrong key).
"""

from __future__ import annotations

import json
import logging
import socket
import struct
import threading
import time
from collections.abc import Callable

from Crypto.Cipher import AES

_LOGGER = logging.getLogger(__name__)

DEFAULT_PORT = 9741

# Static AES-256 key / IV used by every LG "WiFi Speaker" soundbar.
_KEY = b"T^&*J%^7tr~4^%^&I(o%^!jIJ__+a0 k"
_IV = b"'%^Ur7gy$~t+f)%@"

_HEADER = 0x10
_CONNECT_TIMEOUT = 10.0
_MAX_BACKOFF = 30.0

# Message identifiers used by the protocol.
MSG_SPK = "SPK_LIST_VIEW_INFO"
MSG_SETTING = "SETTING_VIEW_INFO"
MSG_EQ = "EQ_VIEW_INFO"
MSG_FUNC = "FUNC_VIEW_INFO"
MSG_PRODUCT = "PRODUCT_INFO"

ALL_GET_MESSAGES = (MSG_SPK, MSG_SETTING, MSG_EQ, MSG_FUNC, MSG_PRODUCT)


def _pad(data: bytes) -> bytes:
    pad_len = 16 - (len(data) % 16)
    return data + bytes([pad_len]) * pad_len


def _unpad(data: bytes) -> bytes:
    return data[: -data[-1]]


def encrypt(payload: dict) -> bytes:
    """Serialize + encrypt a command into a framed packet."""
    raw = _pad(json.dumps(payload).encode("utf-8"))
    encrypted = AES.new(_KEY, AES.MODE_CBC, _IV).encrypt(raw)
    return bytes([_HEADER]) + struct.pack(">I", len(encrypted)) + encrypted


def decrypt(data: bytes) -> dict:
    """Decrypt + parse a frame body into a response dict."""
    decrypted = AES.new(_KEY, AES.MODE_CBC, _IV).decrypt(data)
    return json.loads(_unpad(decrypted).decode("utf-8"))


class LGSoundbarClient:
    """Maintains a persistent connection and pushes decoded messages back.

    ``on_message`` is invoked (from a background thread) with each decoded
    response dict. ``on_availability`` is invoked with ``True``/``False`` as the
    socket connects/drops. Both callbacks must be cheap and thread-safe.
    """

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        on_message: Callable[[dict], None] | None = None,
        on_availability: Callable[[bool], None] | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self._on_message = on_message
        self._on_availability = on_availability
        self._sock: socket.socket | None = None
        self._send_lock = threading.Lock()
        self._closed = False
        self._available = False
        self._thread = threading.Thread(
            target=self._run, name=f"lgsoundbar-{host}", daemon=True
        )
        self._thread.start()

    # -- background connection loop ------------------------------------------

    def _run(self) -> None:
        backoff = 1.0
        while not self._closed:
            try:
                self._open()
                backoff = 1.0
                self._listen()
            except Exception as err:  # noqa: BLE001 - any failure -> reconnect
                self._set_available(False)
                if self._closed:
                    break
                _LOGGER.debug("%s: connection lost (%s); retrying", self.host, err)
                time.sleep(min(backoff, _MAX_BACKOFF))
                backoff *= 2

    def _open(self) -> None:
        sock = socket.create_connection((self.host, self.port), _CONNECT_TIMEOUT)
        sock.settimeout(None)
        with self._send_lock:
            self._sock = sock
        self._set_available(True)
        _LOGGER.debug("%s: connected", self.host)

    def _listen(self) -> None:
        assert self._sock is not None
        while not self._closed:
            header = self._recv_exact(1)
            if header[0] != _HEADER:
                continue
            length = struct.unpack(">I", self._recv_exact(4))[0]
            if length <= 0 or length % 16 != 0:
                continue
            body = self._recv_exact(length)
            try:
                message = decrypt(body)
            except Exception as err:  # noqa: BLE001 - skip undecodable frames
                _LOGGER.debug("%s: undecodable frame (%s)", self.host, err)
                continue
            if self._on_message is not None:
                self._on_message(message)

    def _recv_exact(self, count: int) -> bytes:
        assert self._sock is not None
        buffer = bytearray()
        while len(buffer) < count:
            chunk = self._sock.recv(count - len(buffer))
            if not chunk:
                raise ConnectionError("connection closed by soundbar")
            buffer += chunk
        return bytes(buffer)

    # -- public API ----------------------------------------------------------

    @property
    def available(self) -> bool:
        return self._available

    def send(self, payload: dict) -> None:
        packet = encrypt(payload)
        with self._send_lock:
            sock = self._sock
        if sock is None:
            raise ConnectionError("soundbar not connected")
        sock.sendall(packet)

    def get(self, message: str) -> None:
        self.send({"cmd": "get", "msg": message})

    def set(self, message: str, data: dict) -> None:
        self.send({"cmd": "set", "msg": message, "data": data})

    def request_all(self) -> None:
        for message in ALL_GET_MESSAGES:
            try:
                self.get(message)
            except ConnectionError:
                break

    def close(self) -> None:
        self._closed = True
        with self._send_lock:
            sock = self._sock
            self._sock = None
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass

    def _set_available(self, available: bool) -> None:
        if available == self._available:
            return
        self._available = available
        if self._on_availability is not None:
            self._on_availability(available)


def probe(host: str, port: int = DEFAULT_PORT, timeout: float = 5.0) -> dict:
    """One-shot synchronous fetch of PRODUCT_INFO, for the config flow.

    Returns the product-info ``data`` dict (model name, uuid, mac) or raises
    ``ConnectionError`` if the soundbar can't be reached / doesn't answer.
    """
    with socket.create_connection((host, port), timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(encrypt({"cmd": "get", "msg": MSG_PRODUCT}))
        # Read frames until we get PRODUCT_INFO (the bar may push others first).
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            header = _recv_exact_socket(sock, 1)
            if header[0] != _HEADER:
                continue
            length = struct.unpack(">I", _recv_exact_socket(sock, 4))[0]
            if length <= 0 or length % 16 != 0:
                continue
            message = decrypt(_recv_exact_socket(sock, length))
            if message.get("msg") == MSG_PRODUCT:
                data = message.get("data")
                if isinstance(data, dict):
                    return data
    raise ConnectionError("no PRODUCT_INFO response from soundbar")


def _recv_exact_socket(sock: socket.socket, count: int) -> bytes:
    buffer = bytearray()
    while len(buffer) < count:
        chunk = sock.recv(count - len(buffer))
        if not chunk:
            raise ConnectionError("connection closed by soundbar")
        buffer += chunk
    return bytes(buffer)
