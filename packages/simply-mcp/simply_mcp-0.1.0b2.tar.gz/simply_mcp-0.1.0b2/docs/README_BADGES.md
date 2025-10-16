# README Badges

Add these badges to your README.md to show project status and build health.

## Recommended Badge Section

Add this section near the top of your README.md, right after the title and description:

```markdown
[![CI](https://github.com/Clockwork-Innovations/simply-mcp-py/workflows/CI/badge.svg)](https://github.com/Clockwork-Innovations/simply-mcp-py/actions/workflows/ci.yml)
[![Release](https://github.com/Clockwork-Innovations/simply-mcp-py/workflows/Release/badge.svg)](https://github.com/Clockwork-Innovations/simply-mcp-py/actions/workflows/release.yml)
[![Documentation](https://github.com/Clockwork-Innovations/simply-mcp-py/workflows/Documentation/badge.svg)](https://github.com/Clockwork-Innovations/simply-mcp-py/actions/workflows/docs.yml)
[![PyPI version](https://badge.fury.io/py/simply-mcp.svg)](https://badge.fury.io/py/simply-mcp)
[![Python versions](https://img.shields.io/pypi/pyversions/simply-mcp.svg)](https://pypi.org/project/simply-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![codecov](https://codecov.io/gh/Clockwork-Innovations/simply-mcp-py/branch/main/graph/badge.svg)](https://codecov.io/gh/Clockwork-Innovations/simply-mcp-py)
```

## Badge Breakdown

### GitHub Actions Workflow Badges

**CI Badge**:
```markdown
[![CI](https://github.com/Clockwork-Innovations/simply-mcp-py/workflows/CI/badge.svg)](https://github.com/Clockwork-Innovations/simply-mcp-py/actions/workflows/ci.yml)
```
Shows status of continuous integration tests.

**Release Badge**:
```markdown
[![Release](https://github.com/Clockwork-Innovations/simply-mcp-py/workflows/Release/badge.svg)](https://github.com/Clockwork-Innovations/simply-mcp-py/actions/workflows/release.yml)
```
Shows status of release workflow.

**Documentation Badge**:
```markdown
[![Documentation](https://github.com/Clockwork-Innovations/simply-mcp-py/workflows/Documentation/badge.svg)](https://github.com/Clockwork-Innovations/simply-mcp-py/actions/workflows/docs.yml)
```
Shows documentation build status.

### PyPI Badges

**Version Badge**:
```markdown
[![PyPI version](https://badge.fury.io/py/simply-mcp.svg)](https://badge.fury.io/py/simply-mcp)
```
Shows current PyPI version.

**Python Versions Badge**:
```markdown
[![Python versions](https://img.shields.io/pypi/pyversions/simply-mcp.svg)](https://pypi.org/project/simply-mcp/)
```
Shows supported Python versions.

### License Badge

```markdown
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
```
Shows project license.

### Coverage Badge (if using Codecov)

```markdown
[![codecov](https://codecov.io/gh/Clockwork-Innovations/simply-mcp-py/branch/main/graph/badge.svg)](https://codecov.io/gh/Clockwork-Innovations/simply-mcp-py)
```
Shows code coverage percentage.

## Alternative Badge Styles

### Shields.io Style

```markdown
![CI](https://img.shields.io/github/actions/workflow/status/Clockwork-Innovations/simply-mcp-py/ci.yml?branch=main&label=CI)
![Release](https://img.shields.io/github/actions/workflow/status/Clockwork-Innovations/simply-mcp-py/release.yml?label=Release)
![Python](https://img.shields.io/pypi/pyversions/simply-mcp)
![Version](https://img.shields.io/pypi/v/simply-mcp)
![Downloads](https://img.shields.io/pypi/dm/simply-mcp)
![License](https://img.shields.io/github/license/Clockwork-Innovations/simply-mcp-py)
```

### Compact Version

For a more compact look:

```markdown
[![CI](https://github.com/Clockwork-Innovations/simply-mcp-py/workflows/CI/badge.svg)](https://github.com/Clockwork-Innovations/simply-mcp-py/actions)
[![PyPI](https://badge.fury.io/py/simply-mcp.svg)](https://pypi.org/project/simply-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/simply-mcp.svg)](https://pypi.org/project/simply-mcp/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
```

## Additional Optional Badges

### Downloads

```markdown
![Downloads](https://pepy.tech/badge/simply-mcp)
![Downloads/Month](https://pepy.tech/badge/simply-mcp/month)
![Downloads/Week](https://pepy.tech/badge/simply-mcp/week)
```

### Code Quality

```markdown
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)
```

### Repository Stats

```markdown
![Stars](https://img.shields.io/github/stars/Clockwork-Innovations/simply-mcp-py?style=social)
![Forks](https://img.shields.io/github/forks/Clockwork-Innovations/simply-mcp-py?style=social)
![Issues](https://img.shields.io/github/issues/Clockwork-Innovations/simply-mcp-py)
![Pull Requests](https://img.shields.io/github/issues-pr/Clockwork-Innovations/simply-mcp-py)
```

### Activity

```markdown
![Last Commit](https://img.shields.io/github/last-commit/Clockwork-Innovations/simply-mcp-py)
![Contributors](https://img.shields.io/github/contributors/Clockwork-Innovations/simply-mcp-py)
```

## Custom Badge Configuration

You can customize badge appearance using Shields.io:

```markdown
![Custom](https://img.shields.io/badge/custom-badge-blue?style=flat-square&logo=python)
```

Style options:
- `style=flat` (default)
- `style=flat-square`
- `style=plastic`
- `style=for-the-badge`
- `style=social`

Color options:
- Use color names: `blue`, `green`, `red`, etc.
- Use hex codes: `?color=00ADD8`

## Usage

1. Copy the badge section above
2. Paste it into your README.md
3. Update any URLs if repository location changes
4. Badges will automatically update based on workflow status

## Note

- Badges won't show correct status until first workflow runs
- PyPI badges won't work until first package is published
- Codecov badge requires Codecov integration
- GitHub Actions badges update on each workflow run
