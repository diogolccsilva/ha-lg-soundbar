"""Unit tests for the LG soundbar wire protocol (AES-256-CBC + framing)."""

import struct

import protocol


def test_padding_round_trips_to_block_multiple():
    for text in [b"", b"a", b"a" * 15, b"a" * 16, b"a" * 17, b"x" * 200]:
        padded = protocol._pad(text)
        assert len(padded) % 16 == 0
        assert protocol._unpad(padded) == text


def test_encrypt_frames_then_decrypts_back():
    payload = {
        "cmd": "set",
        "msg": "SETTING_VIEW_INFO",
        "data": {"i_woofer_level": 3},
    }
    packet = protocol.encrypt(payload)

    # Frame: 0x10 + 4-byte big-endian length + body.
    assert packet[0] == 0x10
    length = struct.unpack(">I", packet[1:5])[0]
    body = packet[5:]
    assert len(body) == length
    assert length % 16 == 0

    assert protocol.decrypt(body) == payload


def test_get_payload_shape():
    packet = protocol.encrypt({"cmd": "get", "msg": protocol.MSG_SETTING})
    body = packet[5:]
    assert protocol.decrypt(body) == {"cmd": "get", "msg": "SETTING_VIEW_INFO"}


def test_large_payload_survives_round_trip():
    # SETTING_VIEW_INFO is sizable; make sure multi-block frames are intact.
    payload = {"cmd": "get", "msg": "X", "data": {f"k{i}": i for i in range(50)}}
    body = protocol.encrypt(payload)[5:]
    assert protocol.decrypt(body) == payload


def test_all_get_messages_present():
    assert protocol.MSG_SETTING in protocol.ALL_GET_MESSAGES
    assert protocol.MSG_EQ in protocol.ALL_GET_MESSAGES
    assert protocol.MSG_SPK in protocol.ALL_GET_MESSAGES
