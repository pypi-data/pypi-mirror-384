# Changelog

All notable changes to this project will be documented in this file following
the [Keep a Changelog](https://keepachangelog.com/) format.

## [1.0.0] - 2025-10-15

### Added
- - Scaffolded the `btx_lib_list` Python package with CLI entry points (`btx_lib_list`, `btx-lib-list`, and `python -m btx_lib_list`) and rich-click powered help output.
- Shipped the greeting and failure behaviour helpers (`emit_greeting`, `raise_intentional_failure`, `print_info`) with unit-tested coverage.
- Provisioned the automation suite under `scripts/` supporting build, release, version bumping, and metadata inspection tasks.
- Established the pytest-based test suite for behaviours, CLI commands, scripts, and module metadata.
- Authored the initial documentation set including README, INSTALL, architecture concept overview, and the system design module reference.
- Introduced the `btx_lib_list.lib_list` module with a full suite of list-processing helpers (deduplication, pattern filters, string stripping, chunking) and exported them from the package root.
- Added `tests/test_lib_list.py` covering the new helpers across positive, negative, and edge-path behaviours.

### Changed
- Updated the README and module reference to document the list utilities and their CLI usage examples.
- Trimmed and reorganised `AGENTS.md` to reflect the narrower pre-release scope for contributors.
