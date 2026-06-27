# LG Soundbar over local network — Home Assistant integration

[![hacs][hacs-badge]][hacs] [![validate][validate-badge]][validate-workflow] [![tests][tests-badge]][tests-workflow]

A **local** Home Assistant integration for LG soundbars that talks to the bar
directly over your network (**TCP port 9741**, the legacy "LG Soundbar / WiFi
Speaker" protocol) — **no cloud, no ThinQ account, no phone app**.

It exposes the settings the official app has but the built-in `lg_soundbar`
integration does not — most notably the **per-channel speaker levels**
(subwoofer, center, side, rear, height, dialog) — as proper Home Assistant
controls.

Built and verified against an **LG S95TR** (9.1.5).

## Features

A single Home Assistant **device** per soundbar, with:

- **Media player** — power on/off, volume, mute, input/source, and sound mode.
- **Per-channel level controls** — one `number` per channel your bar reports
  (woofer, center, side, top, rear, rear side, rear top, dialog). Ranges come
  from the soundbar itself.
- **EQ tone** — bass, middle, treble.
- **AV sync** — audio delay (0–300 ms) to fix lip-sync.
- **Sound-processing switches** — Neural:X, Dynamic Range Control, Night mode,
  Auto volume, Auto power, Voice feedback.
- **Real-time updates** — the soundbar *pushes* changes (from the app, remote,
  or front panel), so Home Assistant stays in sync without aggressive polling.

## Supported devices

LG soundbars that speak the local "WiFi Speaker" protocol on TCP `9741`
(SK / SN / S-series, including 2024 models like the **S95TR**). The exact set of
level controls is discovered from each bar, so it adapts to your channel layout.

> Not all LG soundbars expose the same channels; the integration only creates
> controls for the fields your specific model reports.

## Requirements

- Home Assistant **2024.6** or newer.
- The soundbar on the **same local network**, reachable on port `9741`.
  Give it a **static/reserved IP** on your router (the protocol has no reliable
  discovery and a changing IP will break the connection).

## Installation

### HACS (recommended)

1. HACS → **⋮** → **Custom repositories**.
2. Add `https://github.com/diogolccsilva/ha-lg-soundbar` with category
   **Integration**.
3. Search HACS for **LG Soundbar Plus** and **Download** it.
4. **Restart** Home Assistant.

### Manual

Copy `custom_components/lg_soundbar_plus/` into your Home Assistant
`config/custom_components/` directory and restart.

## Configuration

1. **Settings → Devices & Services → + Add Integration**.
2. Search for **LG Soundbar Plus**.
3. Enter the soundbar's **IP address**. It's verified by reading the bar's
   product info.

> If you previously used the built-in **LG Soundbars** (`lg_soundbar`)
> integration for this device, remove it to avoid two integrations driving the
> same bar.

## Notes & limitations

- **Power on/off**: supported directly — the bar stays reachable on Wi-Fi in
  standby and is woken via a "power key" press. (If your bar has Wi-Fi standby
  disabled it won't be reachable when off; then use HDMI-CEC or
  [Wake-on-LAN](https://www.home-assistant.io/integrations/wake_on_lan/).)
- **Sound modes**: the bar advertises its available modes and the integration
  maps known IDs to names (e.g. AI Sound Pro, Clear Voice Pro, Sports, Game);
  unknown IDs show a stable generic label (e.g. `Mode 24`) and still select. A
  bar only switches to modes valid for the current source/content — selecting an
  unsupported one makes the bar fall back to its default (e.g. AI Sound Pro).
  That's the soundbar's own behaviour, not a limitation of the integration.
- **Conditional controls**: the app greys some controls out depending on the
  current audio (e.g. **Dialog level** / "Dialog Control" is only offered with
  DTS:X content). The integration doesn't replicate that UI gating — the bar
  still accepts the write, so the control stays usable in Home Assistant.

## Development

```bash
python -m venv .venv
.venv/Scripts/activate      # Windows
pip install -r requirements_test.txt
ruff check .
pytest
```

The protocol layer (`custom_components/lg_soundbar_plus/protocol.py`) only
depends on `pycryptodome` and is unit-tested in `tests/`.

## Credits

The wire protocol is derived from the Apache-2.0 licensed
[`google/python-temescal`](https://github.com/google/python-temescal). See
[`NOTICE`](NOTICE).

## Disclaimer

This is an unofficial, community integration. "LG" and "ThinQ" are trademarks of
their respective owners. Use at your own risk.

This integration was built with AI assistance and tested on real hardware by the
author.

## License

[MIT](LICENSE)

[hacs]: https://github.com/hacs/integration
[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
[validate-badge]: https://github.com/diogolccsilva/ha-lg-soundbar/actions/workflows/validate.yml/badge.svg
[validate-workflow]: https://github.com/diogolccsilva/ha-lg-soundbar/actions/workflows/validate.yml
[tests-badge]: https://github.com/diogolccsilva/ha-lg-soundbar/actions/workflows/tests.yml/badge.svg
[tests-workflow]: https://github.com/diogolccsilva/ha-lg-soundbar/actions/workflows/tests.yml
