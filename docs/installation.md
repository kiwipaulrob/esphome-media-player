---
title: Install ESPHome Media Player
description: Flash ESPHome Media Player firmware to supported ESP32 touchscreen displays from your browser, then connect it to Wi-Fi and Home Assistant.
---

# Installation

Flash ESPHome Media Player firmware to your ESP32 display directly from your browser. No ESPHome dashboard, YAML editing, or special flashing software required.

::: tip Prefer ESPHome?
If you want to compile and install the firmware yourself, use the [ESPHome Config guide](/advanced/esphome-config).
:::

## What You Need

- **A supported device** from the list below
- **USB-C cable** — must be a data cable, not a charge-only cable
- **A computer** running Chrome or Edge (desktop). Safari and Firefox are not supported for flashing.
- **Home Assistant** running on your network with at least one `media_player` entity

<SupportedDevices />

## Flash firmware

Connect the display to your computer with the USB-C cable, choose your device, then click the install button.

<InstallButton />

::: tip Which cable?
If the install button doesn't detect your device, try a different USB-C cable. Charge-only cables often look the same as data cables, but they cannot be used for the first firmware install.
:::

### Step by Step

1. **Plug in the display** using the USB-C cable. If your computer asks to install drivers, allow it.
2. **Choose your device** above, then click **Install ESPHome Media Player**. A dialog will ask you to choose a serial port — select the one that appeared when you plugged in the display.
3. **Wait for the flash to complete.** This takes a few minutes. You'll see a progress bar. Don't disconnect the cable until it finishes.
4. **The display restarts** and shows the setup screen.

## Connect to Wi-Fi

After flashing, the device needs to connect to your Wi-Fi network.

1. **The display creates a hotspot** called **esphome-media-player**. Connect to it from your phone or laptop.
2. **A setup page opens automatically**. If it doesn't, open a browser and go to `192.168.4.1`.
3. **Choose your Wi-Fi network** from the list and enter your password.
4. **The display reconnects** and joins your network.

::: tip If the hotspot doesn't appear
Power-cycle the display by unplugging and re-plugging the USB-C cable. The hotspot only appears when the device cannot connect to a saved Wi-Fi network.
:::

## Add to Home Assistant

1. Home Assistant should automatically discover the device under **Settings → Devices & Services**. Click **Configure** to add it.

   ![Discovered device](./images/ha-discovered.png)

2. Once added, find the device under **Settings → Devices & Services → ESPHome**.

   ![ESPHome device list](./images/ha-esphome-list.png)

3. Open the settings page by visiting the device IP address directly in your browser, or go to the device in Home Assistant under **Settings → Devices & Services → ESPHome** and click **Visit**. Set **Media Player** to the `media_player` entity you want to control (e.g. `media_player.living_room_speaker`).

   ![ESPHome device page](./images/ha-esphome-device.png)

4. Enable the media player controls for the entity if prompted.

   ![Enable controls](./images/ha-enable-controls.png)

That's it — the screen should start showing now-playing info from your selected media player.

## Next steps

- [Firmware Updates](/features/firmware-updates) — automatic over-the-air updates
- [Settings](/features/settings) — configure brightness, timeouts, and display options
- [Speaker Grouping](/features/speaker-grouping) — set up multi-room speaker control
- [Troubleshooting](/advanced/troubleshooting) — common issues and fixes
