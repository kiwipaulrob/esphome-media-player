---
title: ESPHome Media Player Settings
description: Reference the ESPHome Media Player web settings for media player selection, brightness, idle dimming, screen saver, rotation, and firmware updates.
---

# Settings

Most settings are configurable from the device's built-in web settings page - no YAML or reflashing needed. See [Web Settings](/features/webserver) for how to open it, or go to the device in Home Assistant under **Settings -> Devices & Services -> ESPHome** and click **Visit**.

The web settings page runs on the device's ESPHome web server on port `80`. It uses the project's hosted web UI bundle, so the device needs internet access the first time the browser loads the page. On the 4" ESP32-S3 display, opening the web settings page also shows a **Web settings active** screen on the device while the browser is connected.

Some configuration entities may also appear on the Home Assistant device page, depending on the device model, but the web settings page is the main place to configure current firmware.

<SettingsReference />

See [Firmware Updates](/features/firmware-updates) for full firmware update behavior.
