# Weather Gateway Live Data

Polls `http://<ip>/get_livedata_info`. IP is entered during setup.
Polling interval: number entity on the device (15–3600 s, default 60).

Remove the old `rest:` YAML sensors first. Entity IDs: `sensor.<last IP octet>_weather_gateway_<name>`.
