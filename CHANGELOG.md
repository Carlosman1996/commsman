# Changelog


## [0.3.2] - 2025-07-15

### Added

- Create executables for Linux and Windows on every release.
- Automate deploy procedure using a GitHub action.
- Application Menu with main information.

### Fixed
- Bugfix related to the execution button. When the user tries to stop, it did a strange Stop -> Run -> Stop transition.
- The Execute button is not shown until the response data is received.
- Important bugfixes related to frontend stability: critical errors solved.

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
