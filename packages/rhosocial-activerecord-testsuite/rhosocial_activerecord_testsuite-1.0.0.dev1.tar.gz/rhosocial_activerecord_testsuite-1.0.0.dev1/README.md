# RhoSocial ActiveRecord Test Suite

> **⚠️ Development Stage Notice:** This project is currently under development. Features may be added or removed at any time, and there may be defects or inconsistencies with actual implementations. Therefore, the documentation content is subject to change at any time and is for reference only.

[![PyPI version](https://badge.fury.io/py/rhosocial-activerecord-testsuite.svg)](https://badge.fury.io/py/rhosocial-activerecord-testsuite)
[![Python](https://img.shields.io/pypi/pyversions/rhosocial-activerecord-testsuite.svg)](https://pypi.org/project/rhosocial-activerecord-testsuite/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Overview

This package contains the standardized test suite for the [RhoSocial ActiveRecord](https://github.com/rhosocial/python-activerecord) library. Its primary purpose is to provide a consistent set of test contracts that all official and third-party database backends must implement to ensure compatibility and reliability.

By separating the test definitions from the backend implementations, we can guarantee that all backends adhere to the same core functionalities and behaviors expected by the ActiveRecord interface.

## Testing Philosophy

Our testing strategy is built on three core pillars:

1.  **Feature Tests**: Validate individual functionality points (e.g., `where` queries, `save` methods, `BelongsTo` relationships).
2.  **Real-world Scenarios**: Simulate actual business scenarios to verify complex interactions and data integrity.
3.  **Performance Benchmarks**: Measure and compare backend performance under standardized loads.

## Structure

The test suite is organized into the following main categories, located in `src/rhosocial/activerecord/testsuite/`:

-   `/feature`: Core feature tests.
-   `/realworld`: Complex, real-world application scenarios.
-   `/benchmark`: Performance and load tests.

## Capability-based Testing

The test suite includes an integrated pytest plugin that automatically checks if the current backend supports required capabilities. Tests using the `@requires_capability` decorator will be automatically skipped if the backend doesn't support the required features.

The plugin is registered automatically and available when the package is installed.

## Usage for Backend Developers

If you are developing a database backend for RhoSocial ActiveRecord, you should include this test suite as a development dependency. Your backend's test runner will execute these tests against your implementation, using your provided database schema fixtures.

A typical workflow involves:
1.  Adding `rhosocial-activerecord-testsuite` to your `pyproject.toml`.
2.  Creating database schema fixtures that match the structure required by the tests.
3.  Running the test suite against your backend to identify and fix compatibility issues.
4.  Generating a compatibility report to document your backend's compliance level.

For detailed instructions, please refer to the main project's [testing documentation](https://github.com/rhosocial/python-activerecord/blob/main/tests/rhosocial/activerecord_test/README.md).

## Contributing

Contributions are welcome! Please refer to the main repository's [contribution guidelines](https://github.com/rhosocial/python-activerecord/blob/main/CONTRIBUTING.md).

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.
