# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

## [0.1.8] - 2025-10-16

### Changed

- output nanoseconds in line protocol to improve compatibility with telegraf
- suppress NiceGUI welcome message which generated warnings for line protocol
  readers

## [0.1.7] - 2025-03-25

### Added

- the WebUI now logs measurements to stdout in line protocol format

## [0.1.6] - 2025-03-24

### Added

- history plot for HV channel currents

## [0.1.5] - 2025-02-04

### Fixed

- make compatible with Python 3.8
  - use backport of importlib.resources
  - work around fastapi/starlette bugs leading to 404s for static files

### Changed

- update Github actions

## [0.1.4] - 2024-08-28

### Fixed

- slow leak of NiceGUI one-shot timer objects

## [0.1.3] - 2024-07-08

### Fixed

- Github workflow for PyPi packaging

## [0.1.2] - 2024-07-08

### Fixed

- smoother UX with web UI toggles
- untested refactor of command-line parser

## [0.1.1] - 2024-07-06

### Fixed

- remove non-existing I/O tool

## [0.1] - 2024-07-06

### Changed

- `phantomhv-ctl` usage is now based on subcommands

### Added

- PyPi packaging and documentation on Github pages
- `phantomhv-webui` to complement the existing CLI tool
- `PhantomHVStateBuffer` for buffered high-level access
