# After Publishing Guide

## 📦 Where to Find Your Package

### PyPI Package Page

Once you publish to PyPI, your package will be available at:

**Main URL:** `https://pypi.org/project/annotree/`

This page will show:
- Package description (from your README.md)
- Installation instructions
- Version history
- Download statistics
- Project links
- Dependencies

### Installation for Users

After publishing, anyone can install with:

```bash
# Using pip
pip install annotree

# Using uv (faster)
uv pip install annotree

# Specific version
pip install annotree==0.1.0
```

## 🔄 Updating Your Package

### When to Update

You need to publish a new version when you:
- Fix bugs
- Add features
- Update documentation
- Change dependencies

### How to Update

1. **Update version number** in:
   - `pyproject.toml` → `version = "0.1.1"`
   - `annotree/__init__.py` → `__version__ = "0.1.1"`

2. **Update your changes:**
   ```bash
   # Make your code changes
   git add .
   git commit -m "Release v0.1.1"
   git tag v0.1.1
   git push origin main --tags
   ```

3. **Build and publish:**
   ```bash
   # Clean previous builds
   rm -rf dist/ build/ *.egg-info/
   
   # Build new version
   python -m build
   # or
   uv build
   
   # Publish to PyPI
   python -m twine upload dist/*
   # or
   uv publish
   ```

4. **Your PyPI page will automatically update** with:
   - New version number
   - Updated README
   - New release date
   - Updated metadata

### ⚠️ Important Notes

- **You CANNOT edit an existing version** on PyPI
- **You CANNOT delete a version** (only "yank" it)
- To fix anything, you must upload a NEW version
- Version numbers must always increase (0.1.0 → 0.1.1 → 0.2.0)

## 📚 Documentation Options

### Option 1: GitHub (Easiest)

Just push your repo to GitHub:

```bash
# Create repo on GitHub first, then:
git remote add origin https://github.com/yourusername/annotree.git
git push -u origin main
```

Your docs will be at: `https://github.com/yourusername/annotree/tree/main/docs`

**Pros:**
- ✅ Free and easy
- ✅ Users already expect docs on GitHub
- ✅ Easy to update (just push changes)
- ✅ Markdown renders nicely

**Update docs:**
```bash
# Edit docs
nano docs/QUICKSTART.md

# Commit and push
git add docs/
git commit -m "Update documentation"
git push
```

### Option 2: Read the Docs (Most Professional)

1. **Setup** (one time):
   - Go to https://readthedocs.org/
   - Sign in with GitHub
   - Import your repository
   - It auto-builds from your `docs/` folder

2. **Your docs will be at:**
   - `https://annotree.readthedocs.io/`

3. **Updates are automatic:**
   - Push changes to GitHub
   - Read the Docs rebuilds automatically

**Pros:**
- ✅ Very professional
- ✅ Auto-updates from GitHub
- ✅ Search functionality
- ✅ Versioned docs
- ✅ Free for open source

### Option 3: GitHub Pages

1. **Enable GitHub Pages** in repo settings

2. **Your docs will be at:**
   - `https://yourusername.github.io/annotree/`

3. **Setup:**
   ```bash
   # Create docs site
   pip install mkdocs mkdocs-material
   mkdocs new .
   mkdocs gh-deploy
   ```

## 🔗 Project Links

Update these in your `pyproject.toml`:

```toml
[project.urls]
Homepage = "https://github.com/yourusername/annotree"
Documentation = "https://github.com/yourusername/annotree/tree/main/docs"
# or "https://annotree.readthedocs.io"
# or "https://yourusername.github.io/annotree"
"Bug Reports" = "https://github.com/yourusername/annotree/issues"
"Source" = "https://github.com/yourusername/annotree"
"Changelog" = "https://github.com/yourusername/annotree/releases"
```

These links will appear on your PyPI page!

## 📊 Package Statistics

After publishing, you can track:

### On PyPI
- Total downloads
- Downloads per version
- Downloads per day/week/month
- Python version usage

### Using pypistats

```bash
pip install pypistats
pypistats overall annotree
pypistats recent annotree
```

### Using Libraries.io

View at: `https://libraries.io/pypi/annotree`

Shows:
- Download trends
- Dependents
- Repository statistics

## 🎯 Complete Publishing Workflow

### First Time

```bash
# 1. Update author info in pyproject.toml
nano pyproject.toml  # Change name, email, URLs

# 2. Create GitHub repo
# Go to github.com → New Repository → "annotree"

# 3. Push to GitHub
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/annotree.git
git push -u origin main

# 4. Build package
python -m build

# 5. Publish to PyPI
python -m twine upload dist/*

# 6. Done! Check https://pypi.org/project/annotree/
```

### Future Updates

```bash
# 1. Make changes
nano annotree/annotree.py

# 2. Update version
nano pyproject.toml        # version = "0.1.1"
nano annotree/__init__.py  # __version__ = "0.1.1"

# 3. Commit
git add .
git commit -m "Release v0.1.1: Add new feature"
git tag v0.1.1

# 4. Build and publish
rm -rf dist/ build/
python -m build
python -m twine upload dist/*

# 5. Push to GitHub
git push origin main --tags
```

## 📋 Checklist Before First Publish

- [ ] Update `pyproject.toml` with your info
- [ ] Update `setup.py` with your info
- [ ] Update `annotree/__init__.py` author
- [ ] Create GitHub repository
- [ ] Push code to GitHub
- [ ] Test build locally (`python -m build`)
- [ ] Test on TestPyPI first
- [ ] Publish to PyPI
- [ ] Test installation: `pip install annotree`
- [ ] Update GitHub repo description
- [ ] Add topics/tags to GitHub repo

## 🎉 After Publishing

Your package will be:
- ✅ Installable worldwide: `pip install annotree`
- ✅ Visible on PyPI: `https://pypi.org/project/annotree/`
- ✅ Searchable on PyPI
- ✅ Listed on GitHub (if you add PyPI badge)
- ✅ Trackable with download stats

### Add PyPI Badge to README

```markdown
[![PyPI version](https://badge.fury.io/py/annotree.svg)](https://badge.fury.io/py/annotree)
[![Downloads](https://pepy.tech/badge/annotree)](https://pepy.tech/project/annotree)
```

## 💡 Pro Tips

1. **Use TestPyPI first** - Always test on https://test.pypi.org/ before real PyPI
2. **Tag releases on GitHub** - Makes it easy to track versions
3. **Write CHANGELOG** - Users appreciate knowing what changed
4. **Setup CI/CD** - Auto-publish on GitHub release
5. **Monitor downloads** - See how your package is being used

## 🆘 Common Issues

### "Version already exists"
- You must increment version number
- Cannot replace existing versions

### "README not showing on PyPI"
- Make sure `readme = "README.md"` is in pyproject.toml
- Check README.md has no syntax errors

### "Links not showing"
- Update `[project.urls]` in pyproject.toml
- Republish with new version

### "Want to unpublish"
- Contact PyPI support
- Or "yank" the version (not recommended)
- Better to publish a fix version

## 📞 Getting Help

- **PyPI Help**: https://pypi.org/help/
- **Packaging Guide**: https://packaging.python.org/
- **GitHub Issues**: Your repo's issues page
- **Python Packaging Discord**: https://discord.gg/python

---

**Remember**: Once published, your package is public and permanent! Make sure everything is correct before publishing.
