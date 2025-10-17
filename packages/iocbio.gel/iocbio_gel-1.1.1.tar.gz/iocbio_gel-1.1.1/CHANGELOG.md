# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

## [1.1.1] - 2025-10-16

### Fixed
- Crash while calculating cache size for very large cache

## [1.1.0] - 2025-10-10

### Added
- Support for handling images acquired as a short image sequence by averaging them
- Support for cleaning image cache in Settings
- Automatic installation of ZeroC Ice dependency by install scripts

### Changed
- Updated dependencies to Qt 6.9
- Revised installation scripts and installation documentation

## [1.0.3] - 2024-07-11

### Changed
- Updated dependencies to Qt 6.4.3
- Updated GitLab CI configuration for Windows builds

### Fixed
- Error handling in connecting to OMERO server

## [1.0.2] - 2023-10-10

### Added
- Allow to export figures

### Changed
- Update documentation to clarify available image sources and submission of issues
- Set SQLite as a default database

## [1.0.1] - 2023-05-29

### Fixed
- Save cached background image only if needed

## [1.0.0] - 2023-04-05

### Changed
- Update documentation

## [0.10.0] - 2023-03-29

### Added
- Allow to synchronize measurement region for all lanes

### Changed
- Replace `transfer` column with `ref_time` in Gel table

## [0.9.2] - 2023-03-22

### Added
- Add metadata describing the software to setup.py

## [0.9.1] - 2023-03-20

### Changed
- Reduce zero line default percentile to 0.1%

## [0.9.0] - 2023-03-20

### Changed
- Revise measurement area calculation

### Fixed
- Trigger calculations of measurement areas after changes in background correction

## [0.8.0] - 2022-12-06

### Added
- Help text for image source and database selection
- Allow to add new table rows by clicking on cell with New

### Changed
- Settings key used to indicate image source selection

## [0.7.0] - 2022-11-16

### Added
- Icon and splash screen
- Allow to remove gel from single gel view

### Changed
- Updated dependencies

### Fixed
- Handling of aspect ratios for intensity plots
- Fix export from Postgres

## [0.6.0] - 2022-10-20

### Added
- Add support for curved lanes
- Show application version in window title
- Projects can be used to group gels together
- Support sorting in the tables
- Allow to select location for SQLite database
- Add export to Excel
- Add button to toggle between synced and individual gel image lane widths
- Add image repository backends

### Changed
- Indicate current context on sidebar
- Use bundled icons
- Improve zoom indicator functionality
- Breaking: Adjusted SQL VIEW for reference samples
- Revised graph scrolling
- Revised line addition to gel image

## [0.5.0] - 2022-08-17

### Changed
- Breaking: new database format
- Improved background subtraction
- Model/view separation
- Navigation improvements
- UI changes
