# Release Process

This document describes the automated release process for simply-mcp-py using GitHub Actions.

## Overview

The project uses semantic versioning and supports both beta (pre-release) and stable releases. GitHub Actions automates the entire release process including testing, building, and publishing to PyPI.

## Release Types

### Beta Release (Pre-release)

Beta releases are for testing new features before stable release. Tags containing `beta`, `alpha`, or `rc` are automatically marked as pre-releases.

**Version Format**: `0.1.0-beta`, `0.2.0-alpha.1`, `1.0.0-rc.1`

### Stable Release

Stable releases are production-ready versions intended for general use.

**Version Format**: `0.1.0`, `1.0.0`, `2.1.3`

## Creating a Beta Release

1. **Update version in `pyproject.toml`**
   ```toml
   version = "0.1.0-beta"
   ```

2. **Update `CHANGELOG.md` with release notes**
   ```markdown
   ## [0.1.0-beta] - 2025-10-13

   ### Added
   - New feature descriptions

   ### Changed
   - Changes to existing features

   ### Fixed
   - Bug fixes
   ```

3. **Commit changes**
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: prepare v0.1.0-beta release"
   git push origin main
   ```

4. **Create and push tag**
   ```bash
   git tag v0.1.0-beta
   git push origin v0.1.0-beta
   ```

5. **Automated workflow will:**
   - Run all tests across multiple Python versions (3.10, 3.11, 3.12)
   - Run all tests across multiple OS platforms (Ubuntu, macOS, Windows)
   - Run linting with ruff
   - Run type checking with mypy
   - Build the package
   - Create GitHub Release (marked as pre-release)
   - Publish to PyPI

## Creating a Stable Release

1. **Update version in `pyproject.toml`**
   ```toml
   version = "0.1.0"
   ```

2. **Update `CHANGELOG.md`**
   ```markdown
   ## [0.1.0] - 2025-10-13

   ### Added
   - Feature descriptions
   ```

3. **Commit changes**
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: prepare v0.1.0 release"
   git push origin main
   ```

4. **Create and push tag**
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

5. **Automated workflow publishes as stable release**

## Release Checklist

Before creating a release, ensure:

- [ ] All tests passing locally (`pytest tests/ -v`)
- [ ] Code quality checks pass (`ruff check src/simply_mcp`)
- [ ] Type checking passes (`mypy src/simply_mcp --strict`)
- [ ] CHANGELOG.md updated with release notes
- [ ] Version bumped in pyproject.toml
- [ ] Documentation up to date
- [ ] Examples tested and working
- [ ] No uncommitted changes
- [ ] On main branch with latest changes

## GitHub Secrets Required

The following secrets must be configured in GitHub repository settings:

1. **PYPI_TOKEN**: PyPI API token for publishing packages
   - Go to https://pypi.org/manage/account/token/
   - Create a new API token
   - Add to GitHub: Settings → Secrets → Actions → New repository secret

2. **CODECOV_TOKEN** (Optional): Codecov token for coverage reports
   - Go to https://codecov.io
   - Add repository and get token
   - Add to GitHub: Settings → Secrets → Actions → New repository secret

3. **GITHUB_TOKEN**: Automatically provided by GitHub Actions (no setup needed)

## CI/CD Workflows

### CI Workflow (.github/workflows/ci.yml)

Runs on every push and pull request to main/develop branches:
- Tests across Python 3.10, 3.11, 3.12
- Tests across Ubuntu, macOS, Windows
- Code linting with ruff
- Type checking with mypy
- Package build verification
- Coverage reporting to Codecov

### Release Workflow (.github/workflows/release.yml)

Runs when a version tag is pushed (v*):
- Builds package
- Creates GitHub Release
- Publishes to PyPI
- Automatically determines pre-release vs stable based on tag

### Documentation Workflow (.github/workflows/docs.yml)

Runs on push to main branch:
- Builds documentation with mkdocs
- Deploys to GitHub Pages

## Monitoring Releases

1. **Check GitHub Actions**:
   - Go to repository → Actions tab
   - Monitor workflow runs
   - View logs for any failures

2. **Verify GitHub Release**:
   - Go to repository → Releases
   - Confirm release appears with correct assets

3. **Verify PyPI Publication**:
   - Visit https://pypi.org/project/simply-mcp/
   - Confirm new version is live
   - Test installation: `pip install simply-mcp==0.1.0-beta`

## Rollback Process

If a release has issues:

1. **Delete tag locally and remotely**:
   ```bash
   git tag -d v0.1.0-beta
   git push origin :refs/tags/v0.1.0-beta
   ```

2. **Delete GitHub Release**:
   - Go to repository → Releases
   - Click on release → Delete release

3. **Note**: PyPI releases cannot be deleted, only yanked
   - Go to PyPI project page
   - Manage release → Yank release (prevents new installs)

4. **Fix issues and create new release**:
   - Fix the problems
   - Bump version (e.g., 0.1.0-beta → 0.1.1-beta)
   - Follow release process again

## Version Numbering Guidelines

Follow semantic versioning (semver.org):

- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
  - MAJOR: Breaking changes
  - MINOR: New features (backward compatible)
  - PATCH: Bug fixes (backward compatible)

- **Pre-release identifiers**: `-beta`, `-alpha`, `-rc.1`
  - Use for testing before stable release
  - Example: `0.1.0-beta`, `1.0.0-rc.1`

## Best Practices

1. **Test locally first**: Always run full test suite before releasing
2. **Use beta releases**: Test major changes with beta releases first
3. **Document changes**: Keep CHANGELOG.md up to date
4. **Semantic versioning**: Follow semver principles
5. **Tag messages**: Use annotated tags with messages
   ```bash
   git tag -a v0.1.0 -m "Release version 0.1.0"
   ```
6. **Review workflows**: Check GitHub Actions logs for any warnings
7. **Monitor installations**: Track download statistics on PyPI

## Troubleshooting

### Release workflow fails

- Check GitHub Actions logs for specific error
- Verify all secrets are configured correctly
- Ensure version in pyproject.toml matches tag

### PyPI upload fails

- Verify PYPI_TOKEN is valid and has correct permissions
- Check if version already exists on PyPI (cannot overwrite)
- Ensure package builds successfully (`python -m build`)

### Tests fail in CI

- Run tests locally first: `pytest tests/ -v`
- Check for environment-specific issues
- Review test logs in GitHub Actions

### Documentation deployment fails

- Verify mkdocs.yml is valid
- Check that all documentation files exist
- Ensure [docs] dependencies are installed

## Support

For issues with the release process:
- Open an issue: https://github.com/Clockwork-Innovations/simply-mcp-py/issues
- Review workflow files in `.github/workflows/`
- Check GitHub Actions documentation: https://docs.github.com/en/actions
