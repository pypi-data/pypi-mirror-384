# PyPI Trusted Publishing Setup - Action Required

This document provides the **exact steps** you need to complete to enable PyPI publishing for ParquetFrame.

## ✅ What's Already Done

- ✅ **CI/CD Pipeline**: Complete release workflow configured
- ✅ **Package Configuration**: `pyproject.toml` properly set up
- ✅ **Version Ready**: Set to `0.2.1` for first release
- ✅ **Documentation**: README and CHANGELOG prepared
- ✅ **Release Branch**: `chore/setup-pypi-release` created and pushed

## 🚨 Action Required: PyPI Configuration

**You must complete these steps manually (cannot be automated):**

### Step 1: PyPI Account & Project Setup

1. **Sign in to PyPI**: Go to [https://pypi.org](https://pypi.org)
   - Use the account that has permissions for `parquetframe`

2. **Add Trusted Publisher** (BEFORE first release):
   - Navigate to: [https://pypi.org/manage/account/publishing/](https://pypi.org/manage/account/publishing/)
   - Click **"Add a new pending publisher"**

3. **Enter Exactly These Values**:
   ```
   PyPI Project Name:    parquetframe
   Owner:               leechristophermurray
   Repository:          parquetframe
   Workflow filename:   release.yml
   Environment name:    release
   ```

4. **Click "Add"** - The publisher will show as **"Pending"**

### Step 2: GitHub Environment (Optional but Recommended)

1. **Go to Repository Settings**:
   - [https://github.com/leechristophermurray/parquetframe/settings/environments](https://github.com/leechristophermurray/parquetframe/settings/environments)

2. **Create Environment**:
   - Click "New environment"
   - Name: `release`
   - Optional: Add required reviewers
   - Optional: Restrict to `main` branch only

## 🚀 Ready to Release

**Once PyPI is configured, you can proceed with:**

### Step 3: Create Pull Request
```bash
# The branch is already pushed, so just create PR:
# Go to: https://github.com/leechristophermurray/parquetframe/pull/new/chore/setup-pypi-release
```

### Step 4: Merge and Tag
```bash
# After PR is merged:
git checkout main
git pull origin main
git tag -a v0.2.1 -m "chore(release): v0.2.1 - First PyPI release"
git push origin main --follow-tags
```

### Step 5: Monitor Release
- Watch GitHub Actions: [https://github.com/leechristophermurray/parquetframe/actions](https://github.com/leechristophermurray/parquetframe/actions)
- First run will **complete the PyPI handshake**
- Publisher status will change from "Pending" to "Verified"

## 📦 Expected Results

**After successful release:**
- ✅ Package available at: `https://pypi.org/project/parquetframe/0.2.1/`
- ✅ Installable via: `pip install parquetframe==0.2.1`
- ✅ GitHub release created automatically
- ✅ Publisher verified on PyPI

## 🔍 Verification Commands

**Test installation after release:**
```bash
# Create clean environment
python -m venv test_env
source test_env/bin/activate  # or `test_env\Scripts\activate` on Windows

# Install from PyPI
pip install parquetframe==0.2.1

# Test import
python -c "import parquetframe; print(f'ParquetFrame v{parquetframe.__version__} installed successfully!')"

# Test CLI
pframe --version
```

## ❗ Important Notes

1. **No API Tokens Needed**: Trusted publishing uses GitHub's identity
2. **First Run Completes Setup**: The "Pending" publisher becomes "Verified" after first successful run
3. **Automatic Process**: Once configured, all future releases are automatic via git tags

## 🆘 Troubleshooting

**If the release fails:**
- Check GitHub Actions logs for detailed errors
- Verify PyPI publisher configuration matches exactly
- Ensure the repository has the correct permissions

---

**Next Step**: Complete PyPI trusted publishing setup, then merge the PR and create the v0.2.1 tag!
