# Agent Instructions

## Project context

This repository builds ESPHome firmware and documentation for Home Assistant media
player touchscreen devices. Changes often affect physical hardware, browser-based
installers, firmware release assets, or the public documentation site.

Keep changes focused and device-aware. Prefer existing patterns in `common/`,
`devices/`, `components/`, `docs/`, and `scripts/` over introducing new structure.

## Development workflow

- Use feature branches and worktrees for changes.
- Branch and pull request titles should describe the user-facing change rather
  than the tool used to make it.
- Commit and push changes from the feature branch when the work is ready for a
  pull request.
- Do not edit generated webserver output directly. Update the source and run the
  generator instead.

## Verification

- Run `npm run check:all` for changes that touch docs, scripts, generated
  webserver output, release checks, or package dependencies.
- For firmware changes, compile the affected device config in `builds/`.
- For shared firmware changes under `common/`, `components/`, or release
  tooling, compile all supported device configs before merging when practical.
- If hardware or full firmware compilation cannot be run, state exactly what was
  not verified in the pull request notes.

## Review guidelines

- Focus review comments on serious correctness, upgrade, release, device safety,
  and user-visible regressions.
- Flag changes that could break firmware release assets, OTA updates, manifests,
  or the browser installer.
- Check whether user-facing behavior changes also need documentation updates.
- Check LVGL, display, touch, rotation, backlight, wake/sleep, and screen-saver
  changes against each affected device size and resolution.
- Check Home Assistant media player handling for unavailable entities, missing
  artwork or track metadata, supported feature flags, grouping behavior, and
  source selection edge cases.
- Look for YAML package, substitution, and include changes that unintentionally
  affect every device.
- Treat hard-coded text shown on the physical device as needing translation
  review.
