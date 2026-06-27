# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.6] - 2026-06-27

### Fixed
- **AV sync wire scaling.** The bar stores AV sync as `1`–`30` steps of 10 ms
  each, not the raw millisecond value. The control still shows milliseconds
  (0–300 ms, 10 ms steps) but now divides by 10 before sending (and multiplies
  on read), so the value written to the bar is correct.

## [0.1.5] - 2026-06-27

### Added
- **AV sync** control — a `number` for the audio delay (0–300 ms, 10 ms steps),
  to correct lip-sync. The bar doesn't report bounds for this field, so the
  known LG range is used.
- **Sound-mode names** for newer IDs confirmed on the S95TR: `19` AI Sound Pro,
  `21` Sports, `22` Game, `26` Clear Voice Pro. The equaliser map is now an
  explicit ID→name mapping so newer bars' higher IDs resolve correctly; unknown
  IDs still fall back to a stable generic label.

### Changed
- **Tone controls (bass / middle / treble)** moved back under *Configuration*
  alongside the channel levels (reverts the 0.1.3 placement).

### Notes
- Selecting a sound mode the bar doesn't support for the current source/content
  makes it revert to its default (e.g. AI Sound Pro). This is the soundbar's
  behaviour, not a bug.
- **Voice feedback** (`b_voice_feedback`) is on the roadmap: in the app the
  toggle can be greyed out, implying a pre-condition that must be mirrored before
  it can be exposed reliably.

## [0.1.4] - 2026-06-27

### Fixed
- **Power off.** `b_powerkey` is explicit, not a toggle: `true` powers on,
  `false` powers off (confirmed by app capture). `turn_off` now sends `false`
  instead of `true`, so turning the bar off works. Removed the state guards so
  the command always reaches the bar.

## [0.1.3] - 2026-06-27

### Changed
- **Tone controls (bass / middle / treble)** now appear in the primary
  *Controls* section instead of *Configuration*, grouping them separately from
  the per-channel level sliders (which stay under *Configuration*). Note: Home
  Assistant's device page only has fixed buckets (Controls / Configuration /
  Diagnostic / Sensors); a custom-named "Tone" section can be made on a
  dashboard using a Sections view.

## [0.1.2] - 2026-06-27

### Fixed
- **Speaker level / EQ scaling.** The bar encodes level fields as a 0-based wire
  value (`0` == the channel minimum); the real value is offset by the reported
  `min`. The integration now converts both ways (`displayed = raw + min`,
  `wire = displayed - min`), so sliders show correct values and write correct
  ones. Confirmed by app capture: dragging the woofer (range `-15..6`) to its
  extremes sent raw `21` (=+6) and `0` (=-15). This also corrects symmetric
  channels (rear/center/side) that previously appeared pinned at max when they
  were actually at 0, and the bass tone (raw `12` == +6).

## [0.1.1] - 2026-06-27

### Added
- **Power on/off** on the media player. The bar is woken with a momentary
  "power key" press (`SPK_LIST_VIEW_INFO` → `b_powerkey: true`), captured from
  the official app — `b_powerstatus` is read-only and can't be set directly.
  Works because the soundbar stays reachable on Wi-Fi in standby. Calls are
  guarded by the current power state so they only toggle when needed.

## [0.1.0] - 2026-06-27

Initial release. Local control of LG soundbars over TCP port 9741 (no cloud, no
ThinQ account), built and verified against an **LG S95TR**.

### Added
- Self-contained, AES-encrypted protocol client with full-frame reads and
  automatic reconnect (derived from `google/python-temescal`, Apache-2.0).
- A single soundbar **device** exposing:
  - a **media player** (volume, mute, source, sound mode),
  - **per-channel level** controls created from the channels the bar reports
    (woofer, center, side, top, rear, rear side, rear top, dialog),
  - **EQ tone** controls (bass, middle, treble), and
  - **sound-processing switches** (Neural:X, DRC, Night mode, Auto volume,
    Auto power).
- UI config flow (enter the soundbar IP; it's verified via `PRODUCT_INFO`) and
  an options flow for the safety-net poll interval.
- Real-time state via the soundbar's push updates, with a periodic resync.

### Notes
- Surround channel levels map 1:1. The **woofer** and **bass** values are
  reported on a different scale than their stated min/max; they're clamped to
  the reported range and logged at debug level pending hardware confirmation.
- Newer sound-mode/source IDs that the protocol map doesn't name are shown with
  a stable generic label (e.g. "Mode 26") and still select correctly.
