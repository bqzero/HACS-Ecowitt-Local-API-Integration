"""Constants for Weather Gateway Live Data."""

from __future__ import annotations

DOMAIN = "gw_livedata"

CONF_HOST = "host"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL = 15
MAX_SCAN_INTERVAL = 3600
LIVEDATA_PATH = "/get_livedata_info"
REQUEST_TIMEOUT = 10
