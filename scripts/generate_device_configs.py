#!/usr/bin/env python3
"""Generate catalog-backed public ESPHome dashboard configs."""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path
from typing import Any

from product_model import Device, ROOT, load_devices


REPO_URL = "https://github.com/jtenniswood/esphome-media-player"


def required_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{label} must be a non-empty string")
    return value


def public_config(device: Device) -> str:
    config = device.esphome
    title = required_text(config.get("title"), f"{device.config} esphome.title")
    name = required_text(config.get("name"), f"{device.config} esphome.name")
    friendly_name = required_text(config.get("friendly_name"), f"{device.config} esphome.friendly_name")
    rotation_comments = config.get("rotation_comments", [])
    if not isinstance(rotation_comments, list):
        raise RuntimeError(f"{device.config} esphome.rotation_comments must be a list")

    substitutions = [
        f"# {title}",
        "substitutions:",
        f'  name: "{name}"',
        f'  friendly_name: "{friendly_name}"',
        '  # ha_host: "homeassistant.local"  # Home Assistant hostname or IP (change if HA runs on a different host)',
        '  # ha_port: "8123"  # Home Assistant port (change if HA runs on a non-standard port)',
    ]
    for index, comment in enumerate(rotation_comments, start=1):
        substitutions.append(f"  # {required_text(comment, f'{device.config} esphome.rotation_comments[{index}]')}")
    if "rotation_example" in config:
        rotation_example = required_text(config["rotation_example"], f"{device.config} esphome.rotation_example")
        substitutions.append(f'  # display_rotation: "{rotation_example}"')

    return "\n".join(substitutions) + f"""

esphome:
  name: ${{name}}
  friendly_name: ${{friendly_name}}

# Wifi Setup
wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password

# Packages
packages:
  music_dashboard:
    url: {REPO_URL}
    files: [{device.package_path}]
    ref: main
    refresh: 1s
"""


def generated_configs() -> dict[Path, str]:
    return {
        ROOT / "devices" / device.config / "esphome.yaml": public_config(device)
        for device in load_devices()
    }


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
    parser.add_argument("--check", action="store_true", help="Fail if public ESPHome configs are stale")
    args = parser.parse_args()

    changed = False
    configs = generated_configs()
    if args.check:
        unmanaged = sorted((ROOT / "devices").glob("*/esphome.yaml"))
        unmanaged = [path for path in unmanaged if path not in configs]
        if unmanaged:
            for path in unmanaged:
                print(f"Unmanaged public ESPHome config: {path.relative_to(ROOT)}", file=sys.stderr)
            changed = True
    for path, content in sorted(configs.items()):
        changed = write_or_check(path, content, args.check) or changed
    if args.check and changed:
        print("Public ESPHome configs are stale. Run `npm run device-configs:build`.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
