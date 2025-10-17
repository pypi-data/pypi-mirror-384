# DigitalHub SDK

[![license](https://img.shields.io/badge/license-Apache%202.0-blue)](https://github.com/scc-digitalhub/digitalhub-sdk/LICENSE) ![GitHub Release](https://img.shields.io/github/v/release/scc-digitalhub/digitalhub-sdk)
![Status](https://img.shields.io/badge/status-stable-gold)

The Digitalhub library is a python tool for managing projects, entities and executions in Digitalhub. It exposes CRUD methods to create, read, update and delete entities, tools to execute functions or workflows, collect or store execution results and data.

Explore the full documentation at the [link](https://scc-digitalhub.github.io/sdk-docs/).

## Quick start

To install the Digitalhub, you can use pip:

```bash
pip install digitalhub[full]
```

To be able to create and execute functions or workflows, you need to install the runtime you want to use. The Digitalhub SDK supports multiple runtimes, each with its own installation instructions:

- [Digitalhub SDK Runtime Python](https://github.com/scc-digitalhub/digitalhub-sdk-runtime-python)
- [Digitalhub SDK Runtime Dbt](https://github.com/scc-digitalhub/digitalhub-sdk-runtime-dbt)
- [Digitalhub SDK Runtime Container](https://github.com/scc-digitalhub/digitalhub-sdk-runtime-container)
- [Digitalhub SDK Runtime Kfp](https://github.com/scc-digitalhub/digitalhub-sdk-runtime-kfp)
- [Digitalhub SDK Runtime Hera](https://github.com/scc-digitalhub/digitalhub-sdk-runtime-hera)
- [Digitalhub SDK Runtime Modelserve](https://github.com/scc-digitalhub/digitalhub-sdk-runtime-modelserve)

## Development

See CONTRIBUTING for contribution instructions.

## Security Policy

The current release is the supported version. Security fixes are released together with all other fixes in each new release.

If you discover a security vulnerability in this project, please do not open a public issue.

Instead, report it privately by emailing us at digitalhub@fbk.eu. Include as much detail as possible to help us understand and address the issue quickly and responsibly.

## Contributing

To report a bug or request a feature, please first check the existing issues to avoid duplicates. If none exist, open a new issue with a clear title and a detailed description, including any steps to reproduce if it's a bug.

To contribute code, start by forking the repository. Clone your fork locally and create a new branch for your changes. Make sure your commits follow the [Conventional Commits v1.0](https://www.conventionalcommits.org/en/v1.0.0/) specification to keep history readable and consistent.

Once your changes are ready, push your branch to your fork and open a pull request against the main branch. Be sure to include a summary of what you changed and why. If your pull request addresses an issue, mention it in the description (e.g., “Closes #123”).

Please note that new contributors may be asked to sign a Contributor License Agreement (CLA) before their pull requests can be merged. This helps us ensure compliance with open source licensing standards.

We appreciate contributions and help in improving the project!

## Authors

This project is developed and maintained by **DSLab – Fondazione Bruno Kessler**, with contributions from the open source community. A complete list of contributors is available in the project’s commit history and pull requests.

For questions or inquiries, please contact: [digitalhub@fbk.eu](mailto:digitalhub@fbk.eu)

## Copyright and license

Copyright © 2025 DSLab – Fondazione Bruno Kessler and individual contributors.

This project is licensed under the Apache License, Version 2.0.
You may not use this file except in compliance with the License. Ownership of contributions remains with the original authors and is governed by the terms of the Apache 2.0 License, including the requirement to grant a license to the project.
