# Deployment Guide

This guide covers how to commit, push, and deploy version 0.1.1 using the existing GitHub Actions workflows.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Version Update Process](#version-update-process)
3. [Commit and Push Workflow](#commit-and-push-workflow)
4. [Automated Deployment](#automated-deployment)
5. [Manual Release Process](#manual-release-process)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### 1. Required Tools

```bash
# Install required tools
pip install uv  # Package manager
pip install build twine  # Build tools
```

### 2. GitHub Repository Setup

Ensure your repository has:
- `main` branch as default
- GitHub Actions enabled
- PyPI environment configured (for releases)
- Required secrets: `GITHUB_TOKEN` (automatically provided)

### 3. Local Environment

```bash
# Clone and setup
git clone https://github.com/ArmanAvanesyan/aiogram-cmds.git
cd aiogram-cmds

# Install dependencies
uv sync --all-extras --all-groups
```

## Version Update Process

### Step 1: Update Version Numbers

Update version in **three places** to maintain consistency:

#### 1. Update `pyproject.toml`

```toml
[project]
version = "0.1.1"  # Change from 0.1.0 to 0.1.1
```

#### 2. Update `src/aiogram_cmds/version.py`

```python
__version__ = "0.1.1"  # Change from 0.1.0 to 0.1.1
```

#### 3. Update `CHANGELOG.md`

Add new version entry at the top:

```markdown
# Changelog

## [0.1.1] - 2024-01-XX

### Added
- Enhanced i18n integration with aiogram best practices
- Context-based locale switching in translator adapter
- Pluralization support for translations
- Babel workflow scripts for translation management
- Comprehensive command registration guide

### Changed
- Updated translator protocol to support optional pluralization
- Improved middleware integration with SimpleI18nMiddleware
- Enhanced documentation and examples

### Fixed
- Locale resolution now uses aiogram's with_locale context
- Better fallback handling for missing translations

## [0.1.0] - 2024-01-XX
...
```

### Step 2: Verify Version Consistency

```bash
# Run the version checker
python tools/check_version_tag.py
```

Expected output:
```
🔍 Checking version consistency...

📦 Package version: 0.1.1
📋 PyProject version: 0.1.1
ℹ️  GITHUB_REF not set, skipping git tag check

✅ All versions are consistent!
   Version: 0.1.1
```

## Commit and Push Workflow

### Step 1: Create Feature Branch (Recommended)

```bash
# Create and switch to feature branch
git checkout -b release/0.1.1

# Or use develop branch as base (if following git flow)
git checkout develop
git checkout -b release/0.1.1
```

### Step 2: Stage and Commit Changes

```bash
# Add all changes
git add .

# Commit with conventional commit message
git commit -m "chore: bump version to 0.1.1

- Update pyproject.toml version to 0.1.1
- Update src/aiogram_cmds/version.py to 0.1.1
- Add changelog entry for 0.1.1 release
- Enhanced i18n integration with aiogram best practices
- Added pluralization support and Babel workflow scripts"
```

### Step 3: Push to Remote

```bash
# Push feature branch
git push origin release/0.1.1

# Or push directly to main (if you have permissions)
git push origin main
```

### Step 4: Create Pull Request (if using feature branch)

1. Go to GitHub repository
2. Click "Compare & pull request"
3. Set base branch to `main`
4. Add description:
   ```
   ## Release 0.1.1
   
   ### Changes
   - Enhanced i18n integration with aiogram best practices
   - Context-based locale switching in translator adapter
   - Pluralization support for translations
   - Babel workflow scripts for translation management
   - Comprehensive command registration guide
   
   ### Version Updates
   - pyproject.toml: 0.1.0 → 0.1.1
   - src/aiogram_cmds/version.py: 0.1.0 → 0.1.1
   - Updated CHANGELOG.md
   ```
5. Merge the PR

## Automated Deployment

### GitHub Actions Workflow

The repository has automated workflows that trigger on:

1. **CI Pipeline** (`ci.yml`):
   - Runs on every push to `main`
   - Runs on pull requests
   - Includes quality checks, tests, security audits
   - **Triggers**: Push to main, PR to main

2. **Release Pipeline** (`release.yml`):
   - Runs on version tags (`v*.*.*`)
   - Builds and publishes to PyPI
   - Creates GitHub release
   - **Triggers**: Push of version tag

### Step 1: Create and Push Version Tag

```bash
# Create version tag
git tag v0.1.1

# Push tag to trigger release workflow
git push origin v0.1.1
```

### Step 2: Monitor GitHub Actions

1. Go to GitHub repository → Actions tab
2. Watch the "Release" workflow run
3. Check for any failures in the workflow

### Step 3: Verify Release

1. **PyPI**: Check https://pypi.org/project/aiogram-cmds/
2. **GitHub Release**: Check https://github.com/ArmanAvanesyan/aiogram-cmds/releases
3. **Installation Test**:
   ```bash
   pip install aiogram-cmds==0.1.1
   ```

## Manual Release Process

If automated deployment fails, you can manually release:

### Step 1: Build Package

```bash
# Clean previous builds
rm -rf dist/ build/

# Build package
uv run python -m build
```

### Step 2: Check Package

```bash
# Check package integrity
uv run python -m twine check dist/*
```

### Step 3: Upload to PyPI

```bash
# Upload to PyPI (requires PyPI credentials)
uv run python -m twine upload dist/*

# Or upload to TestPyPI first
uv run python -m twine upload --repository testpypi dist/*
```

### Step 4: Create GitHub Release

1. Go to GitHub repository → Releases
2. Click "Create a new release"
3. Set tag: `v0.1.1`
4. Set title: `Release 0.1.1`
5. Add release notes from CHANGELOG.md
6. Upload built files from `dist/` directory
7. Publish release

## Complete Deployment Script

Create `scripts/deploy.sh` for automated deployment:

```bash
#!/bin/bash
set -e

VERSION="0.1.1"
BRANCH="main"

echo "🚀 Starting deployment for version $VERSION"

# Check if we're on the right branch
current_branch=$(git branch --show-current)
if [ "$current_branch" != "$BRANCH" ]; then
    echo "❌ Not on $BRANCH branch. Current: $current_branch"
    exit 1
fi

# Check if working directory is clean
if ! git diff-index --quiet HEAD --; then
    echo "❌ Working directory is not clean. Please commit or stash changes."
    exit 1
fi

# Verify version consistency
echo "🔍 Checking version consistency..."
python tools/check_version_tag.py

# Run tests
echo "🧪 Running tests..."
uv run pytest tests/ -v

# Create and push tag
echo "🏷️  Creating tag v$VERSION..."
git tag v$VERSION
git push origin v$VERSION

echo "✅ Deployment initiated! Check GitHub Actions for progress."
echo "📦 PyPI: https://pypi.org/project/aiogram-cmds/"
echo "🏷️  GitHub: https://github.com/ArmanAvanesyan/aiogram-cmds/releases"
```

Make it executable and run:

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

## PowerShell Deployment Script (Windows)

Create `scripts/deploy.ps1`:

```powershell
param(
    [string]$Version = "0.1.1",
    [string]$Branch = "main"
)

Write-Host "🚀 Starting deployment for version $Version" -ForegroundColor Green

# Check if we're on the right branch
$currentBranch = git branch --show-current
if ($currentBranch -ne $Branch) {
    Write-Host "❌ Not on $Branch branch. Current: $currentBranch" -ForegroundColor Red
    exit 1
}

# Check if working directory is clean
$status = git status --porcelain
if ($status) {
    Write-Host "❌ Working directory is not clean. Please commit or stash changes." -ForegroundColor Red
    exit 1
}

# Verify version consistency
Write-Host "🔍 Checking version consistency..." -ForegroundColor Yellow
python tools/check_version_tag.py

# Run tests
Write-Host "🧪 Running tests..." -ForegroundColor Yellow
uv run pytest tests/ -v

# Create and push tag
Write-Host "🏷️  Creating tag v$Version..." -ForegroundColor Yellow
git tag "v$Version"
git push origin "v$Version"

Write-Host "✅ Deployment initiated! Check GitHub Actions for progress." -ForegroundColor Green
Write-Host "📦 PyPI: https://pypi.org/project/aiogram-cmds/" -ForegroundColor Cyan
Write-Host "🏷️  GitHub: https://github.com/ArmanAvanesyan/aiogram-cmds/releases" -ForegroundColor Cyan
```

Run with:

```powershell
pwsh scripts/deploy.ps1 -Version "0.1.1"
```

## Troubleshooting

### Common Issues

#### 1. Version Mismatch Error

```
❌ Version mismatch found!
   package: 0.1.1
   pyproject: 0.1.0
```

**Solution**: Update all version files consistently.

#### 2. GitHub Actions Failure

**Check logs for**:
- Permission issues (PyPI environment)
- Build failures
- Test failures

**Solutions**:
- Verify PyPI environment is configured
- Check repository secrets
- Run tests locally first

#### 3. PyPI Upload Failure

```
HTTPError: 400 Client Error: File already exists
```

**Solution**: Version already exists. Either:
- Increment version number
- Use `--skip-existing` flag (if supported)

#### 4. Tag Already Exists

```
fatal: tag 'v0.1.1' already exists
```

**Solution**:
```bash
# Delete local tag
git tag -d v0.1.1

# Delete remote tag
git push origin --delete v0.1.1

# Recreate tag
git tag v0.1.1
git push origin v0.1.1
```

### Verification Commands

```bash
# Check current version
python -c "import sys; sys.path.insert(0, 'src'); from aiogram_cmds.version import __version__; print(__version__)"

# Test installation
pip install aiogram-cmds==0.1.1

# Verify package
python -c "import aiogram_cmds; print(aiogram_cmds.__version__)"
```

## Best Practices

### 1. Pre-Release Checklist

- [ ] All tests pass
- [ ] Version numbers updated consistently
- [ ] CHANGELOG.md updated
- [ ] Documentation updated
- [ ] No breaking changes (or properly documented)
- [ ] Security audit passed

### 2. Release Notes Template

```markdown
## [0.1.1] - 2024-01-XX

### Added
- Feature 1
- Feature 2

### Changed
- Improvement 1
- Improvement 2

### Fixed
- Bug fix 1
- Bug fix 2

### Removed
- Deprecated feature (if any)
```

### 3. Post-Release Tasks

- [ ] Verify PyPI package
- [ ] Test installation in clean environment
- [ ] Update documentation if needed
- [ ] Announce release (if applicable)
- [ ] Monitor for issues

## Quick Commands Summary

```bash
# Update versions
# Edit pyproject.toml, src/aiogram_cmds/version.py, CHANGELOG.md

# Verify consistency
python tools/check_version_tag.py

# Commit and push
git add .
git commit -m "chore: bump version to 0.1.1"
git push origin main

# Create and push tag
git tag v0.1.1
git push origin v0.1.1

# Monitor deployment
# Check GitHub Actions → Release workflow
```

This guide ensures a smooth deployment process for version 0.1.1 using the existing GitHub Actions infrastructure.
