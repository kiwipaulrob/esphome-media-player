#!/usr/bin/env python3
"""Build the custom ESPHome web server JavaScript bundle."""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path
import sys

from product_model import (
    firmware_manifest_slugs,
    web_device_profiles,
    web_setting_default,
    web_setting_options,
    web_settings_entities,
    web_settings_number_limits,
    web_settings_state,
)


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "docs" / "webserver" / "src"
STYLE_PATH = SRC_DIR / "style.css"
TEMPLATE_PATH = SRC_DIR / "app.template.js"
OUT_PATH = ROOT / "docs" / "public" / "webserver" / "app.js"


def js_literal(value: object) -> str:
    return json.dumps(value, separators=(",", ":"))


def build_bundle() -> str:
    css = STYLE_PATH.read_text().rstrip("\n")
    template = TEMPLATE_PATH.read_text()
    replacements = {
        "__MEDIA_PLAYER_CSS__": js_literal(css),
        "__FIRMWARE_MANIFEST_SLUGS__": js_literal(firmware_manifest_slugs()),
        "__WEB_DEVICE_PROFILES__": js_literal(web_device_profiles()),
        "__DEFAULT_SPEAKER_PANEL_TIMEOUT__": js_literal(web_setting_default("speaker_panel_timeout")),
        "__WEB_SETTING_OPTIONS__": js_literal(web_setting_options()),
        "__WEB_SETTINGS_STATE__": js_literal(web_settings_state()),
        "__WEB_SETTINGS_ENTITIES__": js_literal(web_settings_entities()),
        "__WEB_SETTINGS_NUMBER_LIMITS__": js_literal(web_settings_number_limits()),
    }
    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)
    return template


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
    parser.add_argument("--check", action="store_true", help="Fail if generated bundle is stale")
    args = parser.parse_args()

    changed = write_or_check(OUT_PATH, build_bundle(), args.check)
    if args.check and changed:
        print("Generated web server bundle is stale. Run `npm run webserver:build`.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
