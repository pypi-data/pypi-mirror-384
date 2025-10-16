# First Release Checklist

This checklist guides you through creating your first release (v0.1.0-beta) with the newly configured CI/CD pipeline.

## Prerequisites

Before creating the first release, complete these setup steps:

### 1. Configure PyPI Token (REQUIRED)

The release workflow needs a PyPI token to publish packages.

**Steps**:
1. Go to https://pypi.org/manage/account/
2. If you don't have an account, create one
3. Verify your email address
4. Go to https://pypi.org/manage/account/token/
5. Click "Add API token"
   - Token name: `simply-mcp-github-actions`
   - Scope: Select "Entire account" (or specific project after first upload)
6. Click "Add token"
7. **IMPORTANT**: Copy the token immediately (starts with `pypi-`)
8. Go to GitHub repository: https://github.com/Clockwork-Innovations/simply-mcp-py
9. Settings → Secrets and variables → Actions
10. Click "New repository secret"
11. Name: `PYPI_TOKEN`
12. Value: Paste the PyPI token
13. Click "Add secret"

### 2. Configure Codecov (OPTIONAL)

For coverage reporting, you can optionally configure Codecov.

**Steps**:
1. Go to https://codecov.io
2. Sign in with GitHub
3. Add repository: Clockwork-Innovations/simply-mcp-py
4. Copy the repository token
5. Go to GitHub repository settings
6. Settings → Secrets and variables → Actions
7. Click "New repository secret"
8. Name: `CODECOV_TOKEN`
9. Value: Paste the Codecov token
10. Click "Add secret"

**Note**: Coverage will still work without this token, just won't upload to Codecov.

### 3. Enable GitHub Pages (OPTIONAL)

For documentation deployment:

1. Go to GitHub repository settings
2. Pages → Build and deployment
3. Source: "Deploy from a branch"
4. Branch: Select "gh-pages" and "/ (root)"
5. Click "Save"

**Note**: The gh-pages branch will be created automatically on first docs deployment.

### 4. Pre-Release Verification

Run these checks locally to ensure everything works:

```bash
# Navigate to project directory
cd /mnt/Shared/cs-projects/simply-mcp-py

# Run all tests
pytest tests/ -v --cov=src/simply_mcp

# Expected: 752/753 tests passing (one known flaky test)
# Coverage: ~86%

# Run linting
ruff check src/simply_mcp

# Expected: No errors

# Run type checking
mypy src/simply_mcp --strict

# Expected: Success - no type errors

# Build package locally
python -m build

# Expected: Creates dist/ with .whl and .tar.gz files

# Verify package
twine check dist/*

# Expected: All files pass validation
```

## Release Process

### Step 1: Update CHANGELOG.md

Create or update `CHANGELOG.md` in the project root:

```bash
# If CHANGELOG.md doesn't exist, create it
cat > CHANGELOG.md << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0-beta] - 2025-10-13

### Added
- Complete MCP server framework with multiple API styles
- Decorator-based API for simple tool and resource registration
- Functional builder API with method chaining
- Comprehensive CLI with run, list, watch, bundle, and dev commands
- HTTP and SSE transport support
- CORS middleware for cross-origin requests
- Authentication and rate limiting features
- Automatic API detection from server files
- Full type safety with Pydantic models
- 752 passing tests with 86% coverage
- Comprehensive documentation and examples

### Features
- Multi-style API: decorators, builders, and direct server API
- Transport layer with HTTP and SSE support
- Security features: authentication, rate limiting
- Developer experience: hot reloading, auto-detection, bundling
- Production ready: logging, error handling, validation

### Documentation
- API documentation with examples
- CLI usage guides
- Transport configuration guides
- Security implementation guides
- Complete example collection

### Testing
- 752/753 tests passing
- 86% code coverage
- Multi-platform support (Ubuntu, macOS, Windows)
- Multi-version support (Python 3.10, 3.11, 3.12)

[0.1.0-beta]: https://github.com/Clockwork-Innovations/simply-mcp-py/releases/tag/v0.1.0-beta
EOF
```

### Step 2: Verify Version

The version is already set to `0.1.0-beta` in `pyproject.toml`:

```bash
# Verify version
grep "version =" pyproject.toml

# Should show: version = "0.1.0-beta"
```

### Step 3: Commit Changes

```bash
# Stage changes
git add CHANGELOG.md pyproject.toml .github/ docs/

# Commit
git commit -m "chore: prepare v0.1.0-beta release

- Add comprehensive CI/CD workflows
- Configure GitHub Actions for multi-platform testing
- Set up automated releases to PyPI
- Add documentation deployment
- Configure Dependabot for dependency updates
- Update version to 0.1.0-beta"

# Push to main
git push origin main
```

**Wait for CI to complete**: Before tagging, ensure the CI workflow passes on main branch.
- Go to: https://github.com/Clockwork-Innovations/simply-mcp-py/actions
- Wait for "CI" workflow to complete successfully

### Step 4: Create and Push Tag

```bash
# Create annotated tag
git tag -a v0.1.0-beta -m "Release v0.1.0-beta

First beta release of simply-mcp-py framework.

Features:
- Multi-style MCP server API (decorators, builders, direct)
- HTTP and SSE transports with CORS support
- Comprehensive CLI with hot reloading and bundling
- Security features: authentication, rate limiting
- Full type safety and validation
- 752 tests passing, 86% coverage

This is a beta release for testing and feedback."

# Push tag to trigger release workflow
git push origin v0.1.0-beta
```

### Step 5: Monitor Release Workflow

1. Go to GitHub Actions: https://github.com/Clockwork-Innovations/simply-mcp-py/actions
2. You should see "Release" workflow triggered
3. Monitor the workflow progress:
   - Build package
   - Create GitHub Release
   - Publish to PyPI

**Expected Duration**: 3-5 minutes

### Step 6: Verify Release

#### Check GitHub Release
1. Go to: https://github.com/Clockwork-Innovations/simply-mcp-py/releases
2. Verify "v0.1.0-beta" release exists
3. Check that it's marked as "Pre-release"
4. Verify dist files are attached (.whl and .tar.gz)
5. Review auto-generated release notes

#### Check PyPI
1. Go to: https://pypi.org/project/simply-mcp/
2. Verify version 0.1.0-beta is listed
3. Check that installation instructions work:

```bash
# In a fresh virtual environment
python -m venv test-env
source test-env/bin/activate  # or test-env\Scripts\activate on Windows

# Install from PyPI
pip install simply-mcp==0.1.0-beta

# Verify installation
simply-mcp --version
# Expected: simply-mcp, version 0.1.0-beta

# Test basic functionality
simply-mcp list

# Clean up
deactivate
rm -rf test-env
```

### Step 7: Test Installation

Create a simple test to verify the package works:

```bash
# Create test directory
mkdir -p /tmp/test-simply-mcp
cd /tmp/test-simply-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install from PyPI
pip install simply-mcp==0.1.0-beta

# Create simple server
cat > test_server.py << 'EOF'
from simply_mcp import create_server, tool

server = create_server("test-server")

@tool(server)
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    server.run()
EOF

# Test that it imports without errors
python -c "import simply_mcp; print('Import successful!')"

# List tools (should show greet)
simply-mcp list test_server.py

# Clean up
deactivate
cd -
rm -rf /tmp/test-simply-mcp
```

## Post-Release Tasks

### 1. Announce Release

Create announcement message:

```markdown
🎉 simply-mcp v0.1.0-beta is now available!

Simply MCP is a modern Python framework for building Model Context Protocol (MCP) servers with multiple API styles.

## What's New
- Multi-style API: decorators, builders, and direct server access
- HTTP and SSE transports with CORS support
- Comprehensive CLI with hot reloading
- Security features: authentication, rate limiting
- Full type safety and 86% test coverage

## Install
```bash
pip install simply-mcp==0.1.0-beta
```

## Quick Start
```python
from simply_mcp import create_server, tool

server = create_server("my-server")

@tool(server)
def greet(name: str) -> str:
    return f"Hello, {name}!"

if __name__ == "__main__":
    server.run()
```

📚 Docs: https://github.com/Clockwork-Innovations/simply-mcp-py
🐛 Issues: https://github.com/Clockwork-Innovations/simply-mcp-py/issues
⭐ Star us on GitHub!

This is a beta release - feedback welcome!
```

Share this on:
- GitHub Discussions
- Twitter/X
- Reddit (r/Python, r/MachineLearning)
- Hacker News
- LinkedIn

### 2. Monitor for Issues

- Watch GitHub Issues for bug reports
- Monitor PyPI download statistics
- Check CI/CD workflows continue passing
- Review Dependabot PRs

### 3. Update Documentation

If GitHub Pages is enabled:
1. Verify docs deployed: https://clockwork-innovations.github.io/simply-mcp-py/
2. Check all pages render correctly
3. Update links in README if needed

### 4. Plan Next Release

Create issues for:
- Bug fixes discovered during beta
- Feature requests from users
- Documentation improvements
- Test coverage improvements

## Troubleshooting

### Release Workflow Fails

**PyPI Token Invalid**:
```
Error: Invalid credentials
```
**Solution**:
- Verify PYPI_TOKEN is set correctly in GitHub secrets
- Check token hasn't expired
- Ensure token has correct permissions

**Version Already Exists**:
```
Error: File already exists
```
**Solution**:
- Version 0.1.0-beta already published
- Bump version to 0.1.1-beta
- Update pyproject.toml and create new tag

**Build Fails**:
```
Error: Building package failed
```
**Solution**:
- Run `python -m build` locally to reproduce
- Check pyproject.toml configuration
- Verify all files are included in git

### Tag Issues

**Wrong Tag Created**:
```bash
# Delete local tag
git tag -d v0.1.0-beta

# Delete remote tag
git push origin :refs/tags/v0.1.0-beta

# Create correct tag
git tag -a v0.1.0-beta -m "Release message"
git push origin v0.1.0-beta
```

**Tag Points to Wrong Commit**:
```bash
# Delete and recreate tag at correct commit
git tag -d v0.1.0-beta
git checkout <correct-commit-hash>
git tag -a v0.1.0-beta -m "Release message"
git push origin v0.1.0-beta --force
```

### Installation Issues

**Package Not Found**:
- Wait a few minutes for PyPI to index
- Check package name is correct: `simply-mcp`
- Verify release workflow completed successfully

**Import Errors**:
- Check Python version >= 3.10
- Verify all dependencies installed
- Try fresh virtual environment

## Success Criteria

Your first release is successful when:

- [ ] PyPI token configured in GitHub secrets
- [ ] Version updated to 0.1.0-beta in pyproject.toml
- [ ] CHANGELOG.md created with release notes
- [ ] Changes committed and pushed to main
- [ ] CI workflow passed on main branch
- [ ] Tag v0.1.0-beta created and pushed
- [ ] Release workflow completed successfully
- [ ] GitHub Release created and marked as pre-release
- [ ] Package published to PyPI
- [ ] Installation from PyPI works
- [ ] Basic functionality tested

## Next Steps

After successful first release:

1. **Gather Feedback**: Monitor issues and discussions
2. **Plan Stable Release**: Address beta feedback
3. **Improve Documentation**: Based on user questions
4. **Add Examples**: Show real-world use cases
5. **Increase Coverage**: Target 90%+ test coverage
6. **Performance**: Benchmark and optimize
7. **Marketing**: Write blog posts, tutorials

## Additional Resources

- **Release Process**: `docs/RELEASE_PROCESS.md`
- **CI/CD Setup**: `docs/CICD_SETUP.md`
- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **PyPI Publishing**: https://packaging.python.org/en/latest/tutorials/packaging-projects/
- **Semantic Versioning**: https://semver.org/

---

**Ready to Release?** Follow the steps above and create your first beta release!
