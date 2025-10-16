<!-- SPDX-FileCopyrightText: 2025 German Aerospace Center <amiris@dlr.de>

SPDX-License-Identifier: CC0-1.0 -->

# Changelog

## [3.3.2](https://gitlab.com/dlr-ve/esy/amiris/amiris-py/-/tags/v3.3.2) - 2025-10-16
### Fixed
- Fix non-identified java versions due to wrong pattern matching #80 (@dlr-cjs)

## [3.3.1](https://gitlab.com/dlr-ve/esy/amiris/amiris-py/-/tags/v3.3.1) - 2025-08-11
### Fixed
- Fix absolute file path handling for `amiris run` option `-j/--jar` #76 (@dlr_fn)

## [3.3.0](https://gitlab.com/dlr-ve/esy/amiris/amiris-py/-/tags/v3.3.0) - 2025-07-25
### Changed
- Write created protobuf files to the target folder #12 (@dlr-cjs)
- Ensure that results from recursive batch runs are not overwritten #35 (@dlr-cjs)
- Avoid overwriting files when calling run in parallel #47 (@dlr-cjs)
- Update to `fameio>=3.5.1` #74 (@dlr-cjs)

### Added
- Add compatibility checks for Python 3.13 in CI #72 (@dlr-cjs)
- Add package and module docstrings !71 (@dlr-cjs)

## [3.2.1](https://gitlab.com/dlr-ve/esy/amiris/amiris-py/-/tags/v3.2.1) - 2025-05-19
### Fixed
- Fix uncaught validation errors #71 (@dlr-cjs)

## [3.2.0](https://gitlab.com/dlr-ve/esy/amiris/amiris-py/-/tags/v3.2.0) - 2025-04-23
### Changed
- Suppress detailed Exception traceback in console #56 (@dlr_fn @dlr-cjs)
- Update to `fameio>=3.2.0` #67 (@dlr-cjs @dlr_fn)
- Adapt `pyproject.toml` structure to new standard #68 (@dlr-cjs)

### Fixed
- Fix check for write access in download directory #56 (@dlr_fn)

## [3.1.0](https://gitlab.com/dlr-ve/esy/amiris/amiris-py/-/tags/v3.1.0) - 2025-04-07
### Changed
- Mark command line option "install" to be deprecated #64 (@dlr-cjs)
- Make "-j" option in "amiris run" command optional, use existing .jar file in cwd if available #63 (@dlr-cjs)
- Update Readme to state workaround for single flag output options #60 (@dlr_fn)

### Added
- Add "download" synonym for command line option "install" #64 (@dlr-cjs)
- Add pre-commit configuration #34 (@dlr-cjs)

## [3.0.0](https://gitlab.com/dlr-ve/esy/amiris/amiris-py/-/tags/v3.0.0) - 2024-12-04
### Changed
- **Breaking**: Update to `fameio>=3.0.0` #57 (@dlr-cjs @dlr_fn)

## [2.2.1](https://gitlab.com/dlr-ve/esy/amiris/amiris-py/-/tags/v2.2.1) - 2024-08-26
### Changed
- Update to `fameio>=2.3.1` #54 (@dlr-cjs @dlr_fn)

### Fixed
- Fix ignored defaults of time-merging options in fameio #54 (@dlr-cjs @dlr_fn)

## [2.2.0](https://gitlab.com/dlr-ve/esy/amiris/amiris-py/-/tags/v2.2.0) - 2024-08-12
### Changed
- Update to `fameio>=2.3.0` #53 (@dlr-cjs @dlr_fn)

### Added
- Check java version and raise warning if version is not eligible which can be skipped with `--no-checks/-nc` #52 (@dlr-cjs @dlr_fn)

## [2.1.0](https://gitlab.com/dlr-ve/esy/amiris/amiris-py/-/tags/v2.1.0) - 2024-05-28
### Changed
- Update to fameio version 2 #48 (@dlr-cjs)
- Improve CI config with more stages to reduce runner times #46 (@dlr-cjs)

## [2.0.0](https://gitlab.com/dlr-ve/esy/amiris/amiris-py/-/tags/v2.0.0) - 2024-04-04
### Changed
- **Breaking**: Removed support for `python==3.8` #42 (@dlr_fn)
- **Breaking**: Removed support for `fameio<2.0.0` #42 (@dlr_fn)
- Upgrade to `pytest>=8.1` #42 (@dlr-cjs @dlr_fn)
- If output folder is specified, no subfolder with the name of the scenario will be created #44 (@dlr-cjs)
- Loosen dependency restrictions for fameio #39 (@dlr-cjs)
- Replace setup.py with pyproject.toml #13 (@dlr-cjs)

### Added
- Option to use CLI commands as list of strings directly within a script !35 (@maurerle @dlr-cjs @dlr_fn)
- Acknowledgement section in Readme #41 (@dlr-cjs)
- Option to pass through FAME-Io output conversion options #42 (@dlr-cjs)
- PyTests for `python==3.12` #42 (@dlr_fn)

### Fixed
- Fix deprecated `pkg_resources.resource_filename` in `_conduct_model_installation` #42 (@dlr-cjs @dlr_fn)

## [1.3](https://gitlab.com/dlr-ve/esy/amiris/amiris-py/-/tags/v1.3) - 2023-06-13
### Changed
- Updated dependency to latest fameio version #36 (@dlr-cjs)

### Removed
- Removed JDK8 support and updated AMIRIS artifact downloading during install #38 (@dlr-cjs)

## [1.2](https://gitlab.com/dlr-ve/esy/amiris/amiris-py/-/tags/v1.2) - 2023-04-21
### Changed
- When writing outputs during `amiris run`, TimeStep is now converted from Fame TimeStep to datetime by default #30
  (@dlr_fn)
- When writing outputs during `amiris run`, results are merged to hourly values using `fameio merge-time` #31 (@dlr_fn)

### Added
- Added `amiris batch` for running multiple scenarios #32 (@dlr_elghazi @dlr_fn)

## [1.1.4](https://gitlab.com/dlr-ve/esy/amiris/amiris-py/-/tags/v1.1.4) - 2023-02-24
### Added
- Added `-m/--mode` option to `amiris install` for model only `-m/--mode model`
  or [examples](https://gitlab.com/dlr-ve/esy/amiris/examples) only with `-m/--mode examples` #27 (@dlr_fn)

## [1.1.3](https://gitlab.com/dlr-ve/esy/amiris/amiris-py/-/tags/v1.1.3) - 2023-02-20
### Added
- Added option to `-f/--force` install overwriting existing AMIRIS installation #26 (@dlr_fn)

### Fixed
- `amiris run` not working on linux due to improper check of access rights #29 (@dlr_fn @dlr-cjs)

## [1.1.2](https://gitlab.com/dlr-ve/esy/amiris/amiris-py/-/tags/v1.1.2) - 2023-02-07
### Added
- Added check for required Java installation #25 (@dlr_fn)
- Added check for sufficient writing access in directories #18 (@dlr_fn)
- Added `" "` to paths to improve identification of paths in logs

## [1.1.1](https://gitlab.com/dlr-ve/esy/amiris/amiris-py/-/tags/v1.1.1) - 2023-01-27
### Fixed
- `amiris run` not working on Mac OS X #24 (@dlr_fn)

## [1.1](https://gitlab.com/dlr-ve/esy/amiris/amiris-py/-/tags/v1.1) - 2022-12-07
### Changed
- **Breaking**: Compatibility with AMIRIS >= v1.2.3.4
- Moved to new AMIRIS packaging with executable Jar and prepackaged log4j.properties

## [1.0](https://gitlab.com/dlr-ve/esy/amiris/amiris-py/-/tags/v1.0) - 2022-11-02
_Initial release_
