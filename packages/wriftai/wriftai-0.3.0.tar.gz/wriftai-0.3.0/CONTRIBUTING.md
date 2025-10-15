# Contributing to `wriftai-python`

Thank you for your interest in contributing to wriftai-python. This guide will help you get started with the contribution process.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](/CODE_OF_CONDUCT.md) By participating, you are expected to uphold this code.

## Types of Contributions

### Report Bugs

Report bugs at https://github.com/wriftai/wriftai-python/issues

If you are reporting a bug, please include:

- Your operating system name and version.
- Any details about your local setup that might be helpful in troubleshooting.
- Detailed steps to reproduce the bug.

### Fix Bugs

Look through the GitHub issues for bugs.
Anything tagged with "bug" and "help wanted" is open to whoever wants to implement a fix for it.

### Implement Features

Look through the GitHub issues for features.
Anything tagged with "enhancement" and "help wanted" is open to whoever wants to implement it.

### Write Documentation

wriftai-python could always use more documentation, whether as part of the official docs, in docstrings, or even on the web in blog posts, articles, and such.

### Submit Feedback

The best way to send feedback is to file an issue at https://github.com/wriftai/wriftai-python/issues.

If you are proposing a new feature:

- Explain in detail how it would work.
- Keep the scope as narrow as possible, to make it easier to implement.

## Getting Started

Please note this documentation assumes you already have `python`, [`uv`](https://docs.astral.sh/uv/getting-started/installation/) and `git` installed.

1. Fork the `wriftai-python` repo on GitHub.

2. Clone your fork locally:

```bash
git clone git@github.com:your-username/wriftai-python.git
cd wriftai-python
```

3. Setup environment

```bash
make install
```

4. Run all quality control checks

```bash
make check
```

5. Run unit and integration tests:

```bash
make test
```

More specific recipes can be found in the [Makefile](./Makefile).

## Development Workflow

1. Create a new branch for your changes:
   ```bash
   git checkout -b type/description
   # Example: git checkout -b feat/predictions-async
   ```
2. Make your changes following the code style guidelines
3. Add tests for your changes
4. Run the checks and test suite:
   ```bash
   make check && make test
   ```
5. Commit your changes with a descriptive message following this format:

   ```
   fix: fix incorrect prediction polling

   Issue: <issue url>
   ```

   Commit messages should be well formatted, and to make that "standardized", use Conventional Commits. You can follow the documentation on [their website](https://www.conventionalcommits.org).

7. Push your branch to your fork
8. Open a pull request. In your PR description:
   - Clearly describe what changes you made and why
   - Include any relevant context or background
   - List any breaking changes or deprecations
   - Reference related issues or discussions

## Releases

We use [**Release Please**](https://github.com/googleapis/release-please) to automate versioning and changelog generation. More information [here](https://elixirschool.com/blog/managing-releases-with-release-please).

- **Do not manually bump versions or edit the changelog.**
- When pull requests are merged into `main`, Release Please will:
  - Update the changelog and package version automatically.
  - Create a **release PR** when there are user-facing changes based on the [conventional commit prefix](https://www.conventionalcommits.org). The most important prefixes you should have in mind are:
    - fix: which represents bug fixes, and correlates to a SemVer patch.
    - feat: which represents a new feature, and correlates to a SemVer minor.
    - feat!:, or fix!:, refactor!:, etc., which represent a breaking change (indicated by the !) and will result in a SemVer major.
- Once the release PR is merged, a GitHub Release is created and the package is automatically **published to PYPI** from CI.
