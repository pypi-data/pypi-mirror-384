# Publishing to PyPI

This guide explains how to publish the `unik` package to PyPI.

## Prerequisites

1. Create an account on [PyPI](https://pypi.org/) if you don't have one
2. Create an account on [TestPyPI](https://test.pypi.org/) for testing (optional but recommended)
3. Generate an API token for authentication

## Setup

Install the required tools:

```bash
pip install build twine
```

## Building the Package

Build the distribution files:

```bash
python -m build
```

This will create both a source distribution (`.tar.gz`) and a wheel (`.whl`) in the `dist/` directory.

## Testing the Build

Check the built packages:

```bash
twine check dist/*
```

## Publishing to TestPyPI (Recommended First Step)

Test your package on TestPyPI before publishing to the real PyPI:

```bash
twine upload --repository testpypi dist/*
```

Then test installing from TestPyPI:

```bash
pip install --index-url https://test.pypi.org/simple/ unik
```

## Publishing to PyPI

Once you've verified everything works on TestPyPI, publish to PyPI:

```bash
twine upload dist/*
```

You'll be prompted for your PyPI credentials. Alternatively, you can configure a `.pypirc` file or use API tokens.

## Using API Tokens

For better security, use API tokens instead of passwords:

1. Generate a token on [PyPI](https://pypi.org/manage/account/token/)
2. Use it when prompted, or configure it in your `.pypirc` file:

```ini
[pypi]
username = __token__
password = pypi-...  # Your API token
```

## Automated Publishing with GitHub Actions

You can automate the publishing process using GitHub Actions. See the GitHub Actions documentation for setting up a workflow that publishes to PyPI on release.

## Version Updates

Before publishing a new version:

1. Update the version in `pyproject.toml`
2. Update the version in `unik/__init__.py`
3. Update the CHANGELOG (if you maintain one)
4. Create a git tag for the release
5. Build and publish

## Clean Up

To remove old builds before creating new ones:

```bash
rm -rf dist/ build/ *.egg-info
```

Then rebuild with `python -m build`.
