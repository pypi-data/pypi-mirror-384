# Release Guide for QUTEN

## Prerequisites

### 1. Set Up PyPI Accounts

1. Create accounts on:
   - **TestPyPI**: https://test.pypi.org/account/register/
   - **PyPI**: https://pypi.org/account/register/

2. Enable 2FA on both accounts (required)

3. Set up Trusted Publishing (recommended over API tokens):
   - Go to PyPI account settings
   - Add a "pending publisher" for GitHub Actions
   - Owner: `yourusername`
   - Repository: `quten`
   - Workflow: `publish.yml`
   - Environment: (leave empty)

### 2. Configure GitHub Repository

No secrets needed with Trusted Publishing! GitHub Actions will authenticate automatically.

## Release Process

### Automated Release (Recommended)

#### 1. Test on TestPyPI First

```bash
# Trigger manual workflow
gh workflow run publish.yml --field test_pypi=true
```

Or via GitHub UI:
1. Go to **Actions** → **Publish to PyPI**
2. Click **Run workflow**
3. Check "Publish to TestPyPI"
4. Click **Run workflow**

#### 2. Verify TestPyPI Installation

```bash
pip install -i https://test.pypi.org/simple/ quten-optimizer==1.0.0
```

Test it:
```python
from quten import QUTEN
import torch
model = torch.nn.Linear(10, 1)
optimizer = QUTEN(model.parameters())
print("✅ TestPyPI package works!")
```

#### 3. Create GitHub Release

When ready for production:

```bash
# Update version in setup.py and pyproject.toml
# Commit changes
git add setup.py pyproject.toml
git commit -m "Bump version to 1.0.0"
git push

# Create and push tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# Create GitHub release
gh release create v1.0.0 \
  --title "QUTEN v1.0.0 - Production Release" \
  --notes "See CHANGELOG.md for details"
```

Or via GitHub UI:
1. Go to **Releases** → **Draft a new release**
2. Choose tag: `v1.0.0` (create new)
3. Title: `QUTEN v1.0.0 - Production Release`
4. Add release notes (see template below)
5. Click **Publish release**

The GitHub Action will automatically:
- Build the package
- Verify version matches tag
- Run package checks
- Publish to PyPI
- Upload artifacts

### Manual Release (Alternative)

If you prefer manual control:

```bash
# 1. Update version
vim setup.py  # Update __version__
vim pyproject.toml  # Update version

# 2. Clean previous builds
rm -rf build/ dist/ *.egg-info/

# 3. Build package
python -m build

# 4. Check package
twine check dist/*

# 5. Upload to TestPyPI
twine upload --repository testpypi dist/*

# 6. Test installation
pip install -i https://test.pypi.org/simple/ quten-optimizer

# 7. Upload to PyPI (when ready)
twine upload dist/*
```

## Release Notes Template

```markdown
## QUTEN v1.0.0 - Production Release

### 🎉 New Features
- Quantum-inspired optimizer with tunneling mechanism
- Observation-based decoherence for automatic exploration/exploitation balance
- Comprehensive ablation study framework
- Production-ready with full type hints and validation

### 🐛 Bug Fixes
- Fixed state management for sparse parameters
- Removed in-place operations that could break autograd
- Improved numerical stability

### ⚡ Performance Improvements
- ~40% reduction in memory allocations
- Pre-allocated buffers for parameter updates
- Optimized sparse gradient handling

### 📚 Documentation
- Complete README with examples
- Ablation study guide
- GitHub Actions CI/CD integration

### 📦 Installation

\`\`\`bash
pip install quten-optimizer==1.0.0
\`\`\`

### 🔍 Benchmarks

- **Rosenbrock**: 61% better than Adam
- **Classification**: Matches/beats Adam on deep networks
- See [ABLATION_STUDY.md](ABLATION_STUDY.md) for details

### 🙏 Acknowledgments

Thanks to all contributors and the PyTorch team!
```

## Version Numbering

We follow Semantic Versioning (SemVer):
- **MAJOR** (1.x.x): Breaking API changes
- **MINOR** (x.1.x): New features, backwards compatible
- **PATCH** (x.x.1): Bug fixes, backwards compatible

Examples:
- `1.0.0` - First stable release
- `1.1.0` - Add new optimizer variants
- `1.0.1` - Fix bug in sparse parameter handling
- `2.0.0` - Breaking API change

## Pre-release Versions

For testing:
- Alpha: `1.0.0a1`, `1.0.0a2`, ...
- Beta: `1.0.0b1`, `1.0.0b2`, ...
- Release candidate: `1.0.0rc1`, `1.0.0rc2`, ...

## Checklist Before Release

- [ ] All tests pass: `pytest tests/`
- [ ] Ablation study runs successfully
- [ ] Version updated in `setup.py` and `pyproject.toml`
- [ ] CHANGELOG.md updated
- [ ] Documentation up to date
- [ ] Examples in README work
- [ ] GitHub Actions workflows pass
- [ ] TestPyPI installation verified
- [ ] Release notes prepared

## Post-Release

1. **Announce Release**
   - Twitter/social media
   - Reddit (r/MachineLearning)
   - PyTorch forums
   - Papers with Code

2. **Update Documentation**
   - Ensure PyPI page looks correct
   - Update any external documentation

3. **Monitor Issues**
   - Watch for bug reports
   - Respond to installation problems

## Rollback

If something goes wrong:

```bash
# Mark release as pre-release on GitHub
gh release edit v1.0.0 --prerelease

# You cannot delete from PyPI, but can yank
# Login to PyPI and use the web interface to yank the release
```

## Troubleshooting

### "Version already exists" Error
- Increment version number (can't reuse versions on PyPI)
- Use post-release version: `1.0.0.post1`

### Trusted Publishing Not Working
1. Verify publisher configuration matches exactly
2. Check workflow permissions in `.github/workflows/publish.yml`
3. Ensure `id-token: write` permission is set

### Package Not Installing
- Check PyPI page for any errors
- Verify dependencies are available
- Test with `pip install --verbose`

### Build Fails
- Check `python -m build` output
- Verify all required files in MANIFEST.in
- Ensure setup.py has no syntax errors

## Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions for PyPI](https://github.com/pypa/gh-action-pypi-publish)
- [Semantic Versioning](https://semver.org/)

## Support

Questions? Open an issue or discussion on GitHub!
