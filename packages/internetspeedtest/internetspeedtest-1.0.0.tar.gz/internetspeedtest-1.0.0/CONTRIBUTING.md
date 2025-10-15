# Contributing to InternetSpeedTest Python CLI

We love your input! We want to make contributing to InternetSpeedTest Python CLI as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

## Pull Requests

Pull requests are the best way to propose changes to the codebase. We actively welcome your pull requests:

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Any contributions you make will be under the LGPL-3.0 Software License

In short, when you submit code changes, your submissions are understood to be under the same [LGPL-3.0 License](https://choosealicense.com/licenses/lgpl-3.0/) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using GitHub's [issues](https://github.com/internetspeedtest-net/internetspeedtest-cli/issues)

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/internetspeedtest-net/internetspeedtest-cli/issues/new); it's that easy!

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

People *love* thorough bug reports. I'm not even kidding.

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install in development mode:
   ```bash
   pip install -e .
   ```
4. Run tests:
   ```bash
   python -m pytest
   ```

## Code Style

- Follow PEP 8 Python style guidelines
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep functions focused and small
- Use meaningful variable and function names

## Testing

- Write tests for new features
- Ensure existing tests pass
- Test on multiple Python versions (3.7+)
- Test with different server configurations

## Documentation

- Update README.md for user-facing changes
- Update docstrings for API changes
- Add examples for new features
- Keep CHANGELOG.md updated

## License

By contributing, you agree that your contributions will be licensed under the LGPL-3.0 License.

## References

This document was adapted from the open-source contribution guidelines for [Facebook's Draft](https://github.com/facebook/draft-js/blob/a9316a723f9e918afde44dea68b5f9f39b7d9b00/CONTRIBUTING.md).