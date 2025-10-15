# Quick Deployment Guide

## Deploy Version 0.1.1

### Prerequisites
- Git repository with `main` branch
- GitHub Actions enabled
- PyPI environment configured
- Local tools: `uv`, `git`

### Quick Commands

```bash
# 1. Update versions (already done)
# - pyproject.toml: version = "0.1.1"
# - src/aiogram_cmds/version.py: __version__ = "0.1.1"
# - CHANGELOG.md: Added 0.1.1 entry

# 2. Verify version consistency
python tools/check_version_tag.py

# 3. Commit changes
git add .
git commit -m "chore: bump version to 0.1.1

- Enhanced i18n integration with aiogram best practices
- Added pluralization support and Babel workflow scripts
- Updated translator protocol with context-based locale switching
- Added comprehensive command registration guide"

# 4. Push to main
git push origin main

# 5. Create and push version tag
git tag v0.1.1
git push origin v0.1.1
```

### Automated Scripts

**Linux/macOS:**
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

**Windows PowerShell:**
```powershell
pwsh scripts/deploy.ps1 -Version "0.1.1"
```

### What Happens Next

1. **GitHub Actions CI** runs automatically on push to main
2. **Release workflow** triggers on tag `v0.1.1`
3. **Package builds** and uploads to PyPI
4. **GitHub Release** created with assets
5. **Version 0.1.1** available for installation

### Verification

```bash
# Check PyPI
curl -s https://pypi.org/pypi/aiogram-cmds/json | jq '.info.version'

# Test installation
pip install aiogram-cmds==0.1.1

# Verify in Python
python -c "import aiogram_cmds; print(aiogram_cmds.__version__)"
```

### Monitor Progress

- **GitHub Actions**: https://github.com/ArmanAvanesyan/aiogram-cmds/actions
- **PyPI Package**: https://pypi.org/project/aiogram-cmds/
- **GitHub Releases**: https://github.com/ArmanAvanesyan/aiogram-cmds/releases

### Troubleshooting

**Version mismatch:**
```bash
python tools/check_version_tag.py
```

**Tag already exists:**
```bash
git tag -d v0.1.1
git push origin --delete v0.1.1
git tag v0.1.1
git push origin v0.1.1
```

**Workflow failure:**
- Check GitHub Actions logs
- Verify PyPI environment permissions
- Ensure all tests pass locally

---

**Status**: Ready for deployment! 🚀