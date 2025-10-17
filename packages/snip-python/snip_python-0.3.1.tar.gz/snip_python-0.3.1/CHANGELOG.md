# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1]

### Dependencies

- Updated pillow to 12.0.0

### Fixed

- Fixed bug in `ImageSnip.from_array` that caused errors when passing arrays of types other than `uint8`.

## [0.3.0]

### Dependencies

- Updated typer to 0.19.1

### Added

- Extended api layer to support now `books` and `accounts` endpoints.
- Account tokens can now be stored and used to authenticate requests.

### Development

- Added python package specific changelog.
- Added mypy type checking.


## [0.2.2]
