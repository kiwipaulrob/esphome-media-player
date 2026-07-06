#!/usr/bin/env python3
"""Generate catalog-backed ESPHome release build entrypoints."""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

from product_model import Device, ROOT, load_devices


BUILDS_DIR = ROOT / "builds"
REPO = "jtenniswood/esphome-media-player"
PROJECT_NAME = "jtenniswood.media-player"
C6_FIRMWARE_PATH = "network_adapter_esp32c6.bin"
C6_FIRMWARE_SHA256 = "3ccfbc4feb0be29c7f5dbe50b0c5a7f0862f0b0c30fb28e5f5a4e1c2891c53f4"


def normal_build(device: Device) -> str:
    return f"""substitutions:
  name: "media-player"
  friendly_name: "Media Player"
  media_player: ""

esphome:
  name_add_mac_suffix: true

packages:
  music_dashboard: !include ../{device.package_path}

wifi:
  ap:

captive_portal:
"""


def factory_build(device: Device) -> str:
    base = f"""substitutions:
  firmware_version: "0.0.0"

packages:
  core: !include {device.config}.yaml

esphome:
  project:
    name: {PROJECT_NAME}
    version: "${{firmware_version}}"

dashboard_import:
  package_import_url: github://{REPO}/devices/{device.config}/esphome.yaml@main
"""
    if device.chip == "ESP32-P4":
        return (
            base
            + f"""
update:
  - platform: esp32_hosted
    id: c6_firmware_update
    type: embedded
    path: {C6_FIRMWARE_PATH}
    sha256: "{C6_FIRMWARE_SHA256}"

globals:
  - id: c6_boot_checked
    type: bool
    initial_value: 'false'

interval:
  - interval: 10s
    then:
      - if:
          condition:
            lambda: 'return !id(c6_boot_checked);'
          then:
            - lambda: 'id(c6_boot_checked) = true;'
            - if:
                condition:
                  update.is_available: c6_firmware_update
                then:
                  - logger.log: "Updating ESP32-C6 co-processor firmware..."
                  - update.perform: c6_firmware_update
                  - delay: 5s
                  - lambda: 'App.safe_reboot();'
"""
        )
    if device.chip == "ESP32-S3":
        return base + "\nimprov_serial:\n"
    raise RuntimeError(f"Unsupported chip for factory build: {device.chip}")


def generated_builds() -> dict[Path, str]:
    builds: dict[Path, str] = {}
    for device in load_devices():
        add_build(builds, BUILDS_DIR / f"{device.config}.yaml", normal_build(device))
        add_build(builds, BUILDS_DIR / f"{device.config}.factory.yaml", factory_build(device))
        for alias in device.build_aliases or []:
            add_build(builds, BUILDS_DIR / f"{alias}.yaml", normal_build(device))
    return builds


def add_build(builds: dict[Path, str], path: Path, content: str) -> None:
    if path in builds:
        raise RuntimeError(f"Duplicate generated build path: {path.relative_to(ROOT)}")
    builds[path] = content


def write_or_check(path: Path, content: str, check: bool) -> bool:
    old = path.read_text() if path.exists() else ""
    if old == content:
        return False
    if check:
        rel = path.relative_to(ROOT)
        diff = "".join(
            difflib.unified_diff(
                old.splitlines(keepends=True),
                content.splitlines(keepends=True),
                fromfile=f"{rel} (current)",
                tofile=f"{rel} (generated)",
            )
        )
        print(diff, file=sys.stderr)
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if build YAML files are stale")
    args = parser.parse_args()

    changed = False
    builds = generated_builds()
    if args.check:
        unmanaged = sorted(path for path in BUILDS_DIR.glob("*.yaml") if path not in builds)
        if unmanaged:
            for path in unmanaged:
                print(f"Unmanaged build YAML file: {path.relative_to(ROOT)}", file=sys.stderr)
            changed = True
    for path, content in sorted(builds.items()):
        changed = write_or_check(path, content, args.check) or changed
    if args.check and changed:
        print("Build YAML files are stale. Run `npm run builds:build`.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
