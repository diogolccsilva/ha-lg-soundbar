"""Constants for the LG Soundbar Plus integration."""

from __future__ import annotations

DOMAIN = "lg_soundbar_plus"

MANUFACTURER = "LG"
DEFAULT_NAME = "LG Soundbar"

CONF_HOST = "host"
CONF_SCAN_INTERVAL = "scan_interval"

# Pushes keep state fresh in real time; polling is just a safety-net resync.
DEFAULT_SCAN_INTERVAL = 30
MIN_SCAN_INTERVAL = 10
MAX_SCAN_INTERVAL = 600
