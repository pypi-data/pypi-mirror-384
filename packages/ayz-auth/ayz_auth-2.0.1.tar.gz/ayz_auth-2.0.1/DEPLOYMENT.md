# Deployment Guide for ayz-auth

This guide covers how to publish the ayz-auth package to PyPI and how end users will install and use it.

## 🚀 Publishing to PyPI

### Prerequisites
1. **PyPI Account**: Create accounts on both [Test PyPI](https://test.pypi.org/) and [PyPI](https://pypi.org/)
2. **API Tokens**: Generate API tokens for secure publishing
3. **UV Installed**: Ensure UV is installed for building

### Step 1: Build the Package
```bash
# Clean any previous builds
rm -rf dist/ build/ *.egg-info/

# Build the package
uv build

# This creates:
# dist/ayz_auth-0.1.0-py3-none-any.whl
# dist/ayz_auth-0.1.0.tar.gz
```

### Step 2: Test on Test PyPI (Recommended)
```bash
# Install twine if not already installed
uv add --dev twine

# Upload to Test PyPI first
uv run twine upload --repository testpypi dist/*

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ ayz-auth
```

### Step 3: Publish to Production PyPI
```bash
# Upload to production PyPI
uv run twine upload dist/*

# Package will be available at: https://pypi.org/project/ayz-auth/
```

### Step 4: Verify Installation
```bash
# Users can now install with:
pip install ayz-auth

# Or with UV:
uv add ayz-auth
```

## 📋 **Version Management**

### Updating the Version
1. Update version in `pyproject.toml`:
   ```toml
   version = "0.1.1"
   ```

2. Update version in `src/ayz_auth/__init__.py`:
   ```python
   __version__ = "0.1.1"
   ```

3. Rebuild and republish:
   ```bash
   uv build
   uv run twine upload dist/*
   ```

## 🔐 **Security Best Practices**

### Using API Tokens
Create a `.pypirc` file in your home directory:
```ini
[distutils]
index-servers = pypi testpypi

[pypi]
username = __token__
password = pypi-your-api-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-api-token-here
```

### Environment Variables (Alternative)
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-api-token-here
uv run twine upload dist/*
```

## 📊 **Package Metadata**

The package will appear on PyPI with:
- **Name**: `ayz-auth`
- **Description**: "FastAPI middleware for Stytch B2B authentication with Redis caching"
- **Keywords**: fastapi, stytch, authentication, middleware, b2b
- **License**: MIT
- **Python Versions**: 3.8+
- **Dependencies**: Automatically listed from pyproject.toml

## 🔄 **Continuous Deployment**

### GitHub Actions Example
```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install UV
      run: pip install uv
    - name: Build package
      run: uv build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: |
        uv add twine
        uv run twine upload dist/*
```

## 📈 **Package Statistics**

Once published, you can track:
- Download statistics on PyPI
- Usage analytics
- User feedback and issues
- Version adoption rates

## 🛠️ **Maintenance**

### Regular Updates
- Security patches
- Dependency updates
- New features
- Bug fixes

### Deprecation Process
- Mark old versions as deprecated
- Provide migration guides
- Maintain backward compatibility when possible
