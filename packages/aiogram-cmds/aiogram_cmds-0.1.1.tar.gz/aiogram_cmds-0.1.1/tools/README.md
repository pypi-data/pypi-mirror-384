# Development Tools

This directory contains utility tools for aiogram-cmds development and maintenance.

## 📋 Available Tools

### `check_version_tag.py`

**Purpose**: Validates version consistency between package sources and git tags.

**Usage**:
```bash
# Check version consistency (typically run in CI)
python tools/check_version_tag.py
```

**What it validates**:
- Package version (`src/aiogram_cmds/version.py`)
- PyProject version (`pyproject.toml`)
- Git tag version (from `GITHUB_REF`)

**When to use**:
- Before releasing to catch version mismatches
- In CI workflows to prevent inconsistent releases
- When debugging version-related issues

**Exit codes**:
- `0` - All versions are consistent
- `1` - Version mismatch found
- `2` - Error reading version information

**Example output**:
```
aiogram-cmds Version Consistency Checker
==================================================

🔍 Checking version consistency...

📦 Package version: 0.1.0
📋 PyProject version: 0.1.0
🏷️  Git tag version: 0.1.0

✅ All versions are consistent!
   Version: 0.1.0
```

### `gen_tree.py`

**Purpose**: Generates markdown-formatted directory tree for documentation.

**Usage**:
```bash
# Generate directory structure for current directory
python tools/gen_tree.py

# Generate for specific directory
python tools/gen_tree.py examples/

# Generate for project root
python tools/gen_tree.py .
```

**Output**: Creates a clean directory tree that can be:
- Pasted into README.md
- Used in documentation
- Included in contribution guides

**Features**:
- Automatically ignores build artifacts, cache files, and IDE files
- Produces markdown-ready output
- Sorts directories before files alphabetically
- Handles permission errors gracefully

**Example output**:
```markdown
# Directory Structure: aiogram-cmds

```
aiogram-cmds/
├── docs/
│   ├── api/
│   │   ├── core.md
│   │   ├── configuration.md
│   │   └── translator.md
│   ├── tutorials/
│   │   ├── basic-setup.md
│   │   ├── i18n-integration.md
│   │   └── advanced-profiles.md
│   ├── index.md
│   ├── quickstart.md
│   └── ARCHITECTURE.md
├── examples/
│   ├── basic_bot.py
│   ├── i18n_bot.py
│   └── README.md
├── src/
│   └── aiogram_cmds/
│       ├── __init__.py
│       ├── manager.py
│       ├── builder.py
│       └── version.py
├── tests/
│   ├── unit/
│   │   ├── test_builder.py
│   │   ├── test_manager.py
│   │   └── test_policy.py
│   └── conftest.py
├── tools/
│   ├── check_version_tag.py
│   ├── gen_tree.py
│   └── README.md
├── pyproject.toml
├── README.md
└── CHANGELOG.md
```

## 🔧 Integration with CI/CD

### GitHub Actions Integration

Both tools are automatically integrated into our CI/CD workflows:

#### Version Checker
```yaml
# In .github/workflows/release.yml
- name: Check version consistency
  run: python tools/check_version_tag.py
```

#### Directory Generator
```yaml
# In .github/workflows/docs.yml
- name: Generate directory tree
  run: python tools/gen_tree.py > docs/directory-structure.md
```

### Pre-commit Hooks

You can add these tools to pre-commit hooks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: check-version
        name: Check version consistency
        entry: python tools/check_version_tag.py
        language: system
        pass_filenames: false
```

## 🚀 Usage in Development

### Regular Development

```bash
# Check versions before committing
python tools/check_version_tag.py

# Generate fresh directory tree for docs
python tools/gen_tree.py > docs/directory-structure.md
```

### Release Process

```bash
# 1. Update versions in all files
# 2. Check consistency
python tools/check_version_tag.py

# 3. Generate updated documentation
python tools/gen_tree.py > docs/directory-structure.md

# 4. Commit and tag
git add .
git commit -m "chore: bump version to 0.1.0"
git tag v0.1.0
```

### Documentation Updates

```bash
# Generate directory tree for README
python tools/gen_tree.py >> README.md

# Generate for specific sections
python tools/gen_tree.py examples/ >> docs/examples.md
python tools/gen_tree.py src/ >> docs/api-structure.md
```

## 🛠️ Customization

### Adding Ignore Patterns

To ignore additional patterns in `gen_tree.py`, modify the `IGNORE_PATTERNS` set:

```python
IGNORE_PATTERNS: Set[str] = {
    # ... existing patterns ...
    "your_custom_pattern",
    "*.custom_extension",
}
```

### Custom Version Sources

To add new version sources in `check_version_tag.py`, add new functions:

```python
def get_custom_version() -> Optional[str]:
    """Get version from custom source."""
    # Your implementation here
    pass
```

Then integrate it into `check_version_consistency()`.

## 🧪 Testing the Tools

### Test Version Checker

```bash
# Test with consistent versions
python tools/check_version_tag.py

# Test with mismatched versions (temporarily modify version.py)
# Should return exit code 1
```

### Test Directory Generator

```bash
# Test with current directory
python tools/gen_tree.py

# Test with specific directory
python tools/gen_tree.py tests/

# Test with non-existent directory
python tools/gen_tree.py /nonexistent
# Should return exit code 1
```

## 📝 Contributing

### Adding New Tools

1. Create a new Python script in the `tools/` directory
2. Add proper docstring and usage information
3. Include error handling and appropriate exit codes
4. Update this README with tool description
5. Add tests if applicable

### Tool Requirements

- **Python 3.10+** compatibility
- **Clear usage instructions** in docstring
- **Appropriate exit codes** (0=success, 1=error, 2=interrupted)
- **Error handling** for common failure cases
- **Command-line interface** with help/usage information

### Example Tool Template

```python
#!/usr/bin/env python3
"""
Tool description.

Usage:
    python tools/your_tool.py [options]

Exit codes:
    0 - Success
    1 - Error
    2 - Interrupted
"""

import sys
from pathlib import Path


def main() -> int:
    """Main function."""
    try:
        # Your tool logic here
        return 0
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        return 2
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

## 🔍 Troubleshooting

### Common Issues

#### Version Checker
- **"Version file not found"**: Make sure you're running from project root
- **"Could not find __version__"**: Check version.py format
- **"GITHUB_REF not set"**: Normal in local development

#### Directory Generator
- **"No files found"**: All files may be ignored by patterns
- **"Permission denied"**: Some directories may not be readable
- **Empty output**: Check ignore patterns

### Debug Mode

Add debug output to tools:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Related Documentation

- [Contributing Guide](../CONTRIBUTING.md) - Development guidelines
- [Release Process](../docs/release.md) - Release workflow
- [CI/CD Workflows](../.github/workflows/) - Automated workflows

---

**Need help with the tools?** Check the [Troubleshooting Guide](../docs/troubleshooting.md) or [create an issue](https://github.com/ArmanAvanesyan/aiogram-cmds/issues)!