# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-10-15

### Changed

* Using UV for package management including changing repo structure
* Update of development dependencies
* Testing on Python 3.14

## [0.2.1] - 2024-11-22

### Added

* `assert_object` module
    * `IsType` expectation that checks object's type.
    * `Is` expectation that checks object's identity.

## [0.2.0] - 2024-11-13

### Added

* `assert_context` module
    * `exception` parameter accepts `None` value which behaves exactly the same as if the value was not set at all.
    * `exception` accepts `ExceptionMatch` instances which allow specifying not only exception type, but also the value for match parameter for `pytest.raises`.

## [0.1.1] - 2024-11-13

### Fixed

* The `assert_context` module handles `BaseException` subclasses not `Exception` subclasses in all valid places.

## [0.1.0] - 2024-05-17

### Added

* The `assert_context` module provides a context manager to ensure that the behavior of the `with` block aligns with expectations.
* The `assert_object` module allows you to define complex object expectations, enabling verification of its structure and values with a single call.
