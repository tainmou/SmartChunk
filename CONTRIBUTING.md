# Contributing to SmartChunk

Thank you for your interest in improving SmartChunk! This guide will help you set up your development environment, follow our coding conventions, and submit pull requests.

## Development Setup

1. **Fork and clone** the repository.
2. **Create a virtual environment** and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .[tokenizer]
   ```
3. **Run the test suite** to ensure everything is working:
   ```bash
   pytest
   ```

## Coding Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) guidelines.
- Format code with [black](https://black.readthedocs.io/en/stable/):
  ```bash
  black .
  ```
- Lint using [ruff](https://docs.astral.sh/ruff/):
  ```bash
  ruff .
  ```
- Include type hints and docstrings where appropriate.

## Pull Request Workflow

1. Create a feature branch and make your changes.
2. Run `black`, `ruff`, and `pytest` before committing.
3. Commit your work with clear messages and push to your fork.
4. Open a pull request describing your changes and link any relevant issues.
5. Ensure CI checks pass and respond to review feedback.

By contributing, you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

Happy hacking!

