# Publishing to PyPI

This guide explains how to publish pi-bridge to PyPI.

## Prerequisites

1. Install build tools:
```bash
pip install build twine
```

2. Create accounts:
   - [PyPI](https://pypi.org/account/register/)
   - [TestPyPI](https://test.pypi.org/account/register/) (for testing)

3. Create API tokens:
   - Go to Account Settings → API tokens
   - Create a token for uploading

## Building the Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build the package
python -m build
```

This creates:
- `dist/pi-bridge-1.0.0.tar.gz` (source distribution)
- `dist/pi-bridge-1.0.0-py3-none-any.whl` (wheel distribution)

## Testing on TestPyPI (Recommended First)

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ pi-bridge
```

## Publishing to PyPI

```bash
# Upload to PyPI
python -m twine upload dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: (paste your API token)

## Verify Installation

```bash
pip install pi-bridge
pi-bridge --help
```

## Version Management

Update version in `pyproject.toml`:
```toml
[project]
version = "1.0.1"  # Increment for new releases
```

Follow [Semantic Versioning](https://semver.org/):
- MAJOR.MINOR.PATCH (e.g., 1.0.0)
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

## Checklist Before Publishing

- [ ] Update version in `pyproject.toml`
- [ ] Update CHANGELOG.md (if you create one)
- [ ] Test installation locally: `pip install -e .`
- [ ] Run tests (if you have them)
- [ ] Build package: `python -m build`
- [ ] Test on TestPyPI first
- [ ] Create git tag: `git tag v1.0.0 && git push --tags`
- [ ] Upload to PyPI: `python -m twine upload dist/*`

## Updating an Existing Package

1. Make your changes
2. Increment version in `pyproject.toml`
3. Rebuild: `python -m build`
4. Upload: `python -m twine upload dist/*`

## Troubleshooting

**"File already exists"**: You can't overwrite versions on PyPI. Increment the version number.

**Import errors after install**: Make sure package structure is correct and `__init__.py` exists in `pi-bridge_tool/`.

**Missing dependencies**: Check `pyproject.toml` dependencies section.

