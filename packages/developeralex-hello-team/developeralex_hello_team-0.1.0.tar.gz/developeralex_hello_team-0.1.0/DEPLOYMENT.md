# Deployment Guide for PyPI

This guide will help you deploy the `hello-team` package to PyPI.

## Prerequisites

1. Create an account on PyPI: https://pypi.org/account/register/
2. (Optional but recommended) Create an account on TestPyPI: https://test.pypi.org/account/register/
3. Install required tools (already installed if you built the package):
   ```bash
   pip install build twine
   ```

## Step 1: Build the Package

The distribution files have already been created in the `dist/` directory:
- `hello_team-0.1.0-py3-none-any.whl` (wheel file)
- `hello-team-0.1.0.tar.gz` (source distribution)

If you need to rebuild:
```bash
python3 -m build --no-isolation
```

## Step 2: Test on TestPyPI (Recommended)

Before uploading to the real PyPI, test on TestPyPI:

```bash
twine upload --repository testpypi dist/*
```

You'll be prompted for your TestPyPI username and password.

To install from TestPyPI and test:
```bash
pip install --index-url https://test.pypi.org/simple/ hello-team
```

## Step 3: Upload to PyPI

Once you've verified everything works on TestPyPI, upload to the real PyPI:

```bash
twine upload dist/*
```

You'll be prompted for your PyPI username (developeralex) and password.

## Step 4: Verify Installation

After uploading, verify that the package can be installed:

```bash
pip install hello-team
```

## Using API Tokens (Recommended for Security)

Instead of using username/password, you can use API tokens:

1. Go to your PyPI account settings: https://pypi.org/manage/account/
2. Scroll to "API tokens" and click "Add API token"
3. Give it a name and select the scope
4. Copy the token (it starts with `pypi-`)

Use the token when uploading:
```bash
twine upload -u __token__ -p pypi-AgEIcHlwaS5vcmcC... dist/*
```

Or create a `~/.pypirc` file:
```ini
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcC...
```

## Troubleshooting

- **Error: File already exists**: You can't re-upload the same version. Increment the version number in `setup.py`, `pyproject.toml`, and `hello_team/__init__.py`, then rebuild.
- **Error: Invalid username/password**: Make sure you're using the correct credentials for PyPI (not TestPyPI).
- **403 Forbidden**: You don't have permission to upload this package name. Make sure the package name is available.

## Version Updates

To release a new version:
1. Update the version in:
   - `hello_team/__init__.py` (line 8: `__version__ = "0.1.0"`)
   - `setup.py` (line 8: `version="0.1.0"`)
   - `pyproject.toml` (line 6: `version = "0.1.0"`)
2. Rebuild: `python3 -m build --no-isolation`
3. Upload: `twine upload dist/*` (upload only the new version files)
