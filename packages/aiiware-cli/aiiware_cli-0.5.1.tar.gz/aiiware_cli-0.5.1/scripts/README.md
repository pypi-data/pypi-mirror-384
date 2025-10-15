# 🚀 Release Scripts

Streamlined tools for building and releasing the a2py package.

## Quick Usage

### Method 1: Python Script (Recommended)
```bash
# Build only (no upload)
uv run python scripts/release.py build

# Build + upload to test PyPI
uv run python scripts/release.py test

# Build + upload to production PyPI (with confirmation)
uv run python scripts/release.py prod

# Interactive workflow: test → confirm → production
uv run python scripts/release.py all
```

### Method 2: Bash Shortcut
```bash
# Same functionality, shorter commands
./scripts/build.sh           # build only
./scripts/build.sh test      # test PyPI
./scripts/build.sh prod      # production PyPI
./scripts/build.sh all       # interactive workflow
```

## What the Script Does

1. **Shows current version** from `aii --version`
2. **Cleans previous builds** (removes `dist/`, `build/`, `*.egg-info`)
3. **Builds package** using `uv build`
4. **Uploads** to test/production PyPI using `twine`
5. **Provides install commands** for testing

## Prerequisites

Make sure you have:
- PyPI API tokens set up in `~/.pypirc`
- `twine` installed (script will install it via `uv` if needed)

## API Token Setup

Create `~/.pypirc`:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your_production_token_here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your_test_token_here
```

Get tokens:
- **Test PyPI**: https://test.pypi.org/manage/account/token/
- **Production PyPI**: https://pypi.org/manage/account/token/

## Example Workflow

```bash
# 1. Build and test locally
uv run python scripts/release.py build

# 2. Upload to test PyPI and verify
uv run python scripts/release.py test

# 3. Test install: pip install --index-url https://test.pypi.org/simple/ a2py

# 4. If good, upload to production
uv run python scripts/release.py prod
```

## Options

- `--no-clean`: Skip cleaning previous builds
- `--help`: Show usage information

## Benefits

✅ **Fast iteration** - no GitHub Actions wait time
✅ **Local testing** - verify before committing
✅ **Safety checks** - confirmation prompts for production
✅ **Clear output** - easy to see what's happening
✅ **Error handling** - stops on failures with clear messages