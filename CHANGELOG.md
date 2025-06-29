# Changelog

## [0.2.0] - 2025-06-29

### Added

- Decouple frontend from backend. The interaction is done using an API.
- The item last result to show in GUI is calculated from the last execution in which it was run.

### Fixed

- Qtimer(500) must be run only while execution is running. The collection results tree does not allow to expand because it is constantly reloaded.

## [0.1.0] - 2025-06-08

### Added

- Client mode for Modbus TCP and RTU protocols.
- Run requests and collections.
- Continuous monitoring.
