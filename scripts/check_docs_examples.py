#!/usr/bin/env python3
"""Validate catalog-backed values in documentation YAML examples."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from product_model import Device, ROOT, load_devices


DOCS_DIR = ROOT / "docs"
YAML_FENCE_RE = re.compile(r"```ya?ml\n(?P<body>.*?)\n```", re.DOTALL)
PACKAGE_PATH_RE = re.compile(r"files:\s*\[\s*(?P<path>devices/[^\]\s]+?\.ya?ml)\s*\]")
DOC_PACKAGE_PATH_RE = re.compile(r"devices/[A-Za-z0-9_./-]+?packages(?:-[A-Za-z0-9_-]+)?\.ya?ml")
SCALAR_RE_TEMPLATE = r"^\s*{key}:\s*['\"]?(?P<value>[^'\"\n#]+?)['\"]?\s*(?:#.*)?$"
ROTATION_VALUES = {"0", "90", "180", "270"}


class DocsExampleError(RuntimeError):
    pass


def scalar_value(block: str, key: str) -> str | None:
    match = re.search(SCALAR_RE_TEMPLATE.format(key=re.escape(key)), block, re.MULTILINE)
    return match.group("value").strip() if match else None


def markdown_files() -> list[Path]:
    return sorted(DOCS_DIR.rglob("*.md"))


def validate_snippet(path: Path, block: str, devices_by_package: dict[str, Device]) -> str | None:
    package_match = PACKAGE_PATH_RE.search(block)
    if not package_match:
        return None

    package_path = package_match.group("path")
    device = devices_by_package.get(package_path)
    if device is None:
        raise DocsExampleError(f"{path.relative_to(ROOT)} contains unknown package path {package_path}")

    expected = device.esphome
    for key in ("name", "friendly_name"):
        value = scalar_value(block, key)
        if value is not None and value != expected[key]:
            raise DocsExampleError(
                f"{path.relative_to(ROOT)} uses {key}={value!r} for {package_path}; expected {expected[key]!r}"
            )

    rotation = scalar_value(block, "display_rotation")
    if rotation is not None and rotation not in ROTATION_VALUES:
        raise DocsExampleError(
            f"{path.relative_to(ROOT)} uses unsupported display_rotation={rotation!r}; "
            f"expected one of {sorted(ROTATION_VALUES)}"
        )

    return package_path


def check_docs_examples() -> None:
    devices = load_devices()
    devices_by_package: dict[str, Device] = {}
    default_package_paths: set[str] = set()
    for device in devices:
        devices_by_package[device.package_path] = device
        default_package_paths.add(device.package_path)
        for package_path in device.alternate_package_paths or []:
            devices_by_package[package_path] = device
    documented_package_paths: dict[Path, set[str]] = {}

    for path in markdown_files():
        text = path.read_text()
        for package_path in DOC_PACKAGE_PATH_RE.findall(text):
            if package_path not in devices_by_package:
                raise DocsExampleError(f"{path.relative_to(ROOT)} references unknown package path {package_path}")

        for match in YAML_FENCE_RE.finditer(text):
            package_path = validate_snippet(path, match.group("body"), devices_by_package)
            if package_path is not None:
                documented_package_paths.setdefault(path, set()).add(package_path)

    manual_config = documented_package_paths.get(DOCS_DIR / "advanced" / "esphome-config.md", set())
    missing_manual = sorted(default_package_paths - manual_config)
    if missing_manual:
        raise DocsExampleError(
            "docs/advanced/esphome-config.md is missing manual config examples for "
            f"{missing_manual}"
        )


def main() -> int:
    try:
        check_docs_examples()
    except DocsExampleError as exc:
        print(f"Documentation example check failed: {exc}", file=sys.stderr)
        return 1
    print("Documentation example checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
