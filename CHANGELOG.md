# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
