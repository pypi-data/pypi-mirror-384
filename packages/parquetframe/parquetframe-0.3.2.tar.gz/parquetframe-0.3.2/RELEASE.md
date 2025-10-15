# Release Process

This document describes the automated release process for ParquetFrame and includes instructions for maintainers.

## Overview

ParquetFrame uses a fully automated release process that is triggered when a new tag is pushed to the repository. The process includes:

1. **Automated Testing** - Full test suite across multiple Python versions
2. **Package Building** - Creates both wheel and source distributions
3. **PyPI Publishing** - Publishes to both Test PyPI and production PyPI
4. **GitHub Release** - Creates a GitHub release with changelog and artifacts
5. **Announcements** - Placeholder for future notification integrations

## Prerequisites

### PyPI Trusted Publishing Setup

The release process uses PyPI's trusted publishing feature (no API keys needed). To set this up:

1. Go to [PyPI Trusted Publishers](https://pypi.org/manage/account/publishing/)
2. Add a new trusted publisher with these settings:
   - **Owner**: `leechristophermurray`
   - **Repository name**: `parquetframe`
   - **Workflow filename**: `release.yml`
   - **Environment name**: `release`

### Repository Secrets

No repository secrets are needed thanks to trusted publishing, but ensure the following repository settings:

- **Actions permissions**: Allow GitHub Actions to create and approve pull requests
- **Environments**: Create a `release` environment for additional protection (optional but recommended)

## Release Process

### 1. Prepare Release

Before creating a release, ensure:

- [ ] All desired features/fixes are merged to `main`
- [ ] `CHANGELOG.md` is updated with the new version
- [ ] Version is bumped in `pyproject.toml` and `src/parquetframe/__init__.py`
- [ ] All tests are passing
- [ ] Documentation is updated

### 2. Create Release Tag

The release process is triggered by pushing a version tag:

```bash
# Ensure you're on main and up to date
git checkout main
git pull origin main

# Create and push the tag (replace X.Y.Z with actual version)
git tag -a vX.Y.Z -m "Release vX.Y.Z: Brief description"
git push origin vX.Y.Z
```

### 3. Automated Release Workflow

Once the tag is pushed, the release workflow automatically:

1. **Runs Tests**: Tests the package on Python 3.9, 3.11, and 3.13
2. **Verifies Version**: Ensures the tag version matches `pyproject.toml`
3. **Builds Package**: Creates wheel and source distributions
4. **Publishes to Test PyPI**: For validation (if it's a tag push)
5. **Publishes to PyPI**: Main distribution
6. **Creates GitHub Release**: With changelog and downloadable artifacts
7. **Announces**: Logs release information

### 4. Manual Verification

After the workflow completes, verify:

- [ ] Package is available on [PyPI](https://pypi.org/project/parquetframe/)
- [ ] GitHub release is created with correct artifacts
- [ ] Installation works: `pip install parquetframe==X.Y.Z`

## Version Numbering

ParquetFrame follows [Semantic Versioning](https://semver.org/):

- **Major** (`X.0.0`): Breaking changes
- **Minor** (`X.Y.0`): New features, backwards compatible
- **Patch** (`X.Y.Z`): Bug fixes, backwards compatible

## Workflow Files

The release process is defined in these GitHub Actions workflows:

- **`.github/workflows/release.yml`** - Main release workflow
- **`.github/workflows/test.yml`** - Continuous testing
- **`.github/workflows/docs.yml`** - Documentation deployment

## Troubleshooting

### Version Mismatch Error

If the workflow fails with a version mismatch:

```bash
# Fix version in pyproject.toml and __init__.py
# Delete the incorrect tag
git tag -d vX.Y.Z
git push origin --delete vX.Y.Z

# Create correct tag
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

### PyPI Publishing Fails

Common issues:

1. **Trusted publishing not configured**: Set up trusted publishing on PyPI
2. **Version already exists**: Use `skip-existing: true` (already configured)
3. **Package validation errors**: Check `twine check` output in logs

### Test Failures

If tests fail during release:

1. Review test logs in GitHub Actions
2. Fix issues and create a patch release
3. Never skip tests for releases

## Manual Release (Emergency)

In rare cases where automated release fails:

```bash
# Build locally
python -m build

# Check package
twine check dist/*

# Upload to PyPI (requires API token)
twine upload dist/*
```

## Post-Release Tasks

After a successful release:

- [ ] Update project board/milestones
- [ ] Announce on relevant channels (Twitter, mailing lists, etc.)
- [ ] Update documentation site if needed
- [ ] Monitor for issues and user feedback

## Release Schedule

- **Major releases**: As needed for breaking changes
- **Minor releases**: Monthly or when significant features are ready
- **Patch releases**: As needed for critical bug fixes

## Contact

For questions about the release process, contact the maintainers or open an issue on GitHub.
