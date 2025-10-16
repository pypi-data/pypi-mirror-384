# PyPI Trusted Publishing Setup

This document provides step-by-step instructions for setting up PyPI trusted publishing for the ParquetFrame project.

## Why Trusted Publishing?

Trusted publishing allows GitHub Actions to publish to PyPI without storing API tokens as secrets. It's more secure and easier to maintain.

## Setup Instructions

### 1. PyPI Account Setup

1. **Create/Login to PyPI Account**
   - Go to [PyPI](https://pypi.org) and ensure you have an account
   - Make sure you have maintainer permissions for the `parquetframe` project

### 2. Configure Trusted Publisher

1. **Navigate to Trusted Publishing**
   - Go to [PyPI Account Publishing Settings](https://pypi.org/manage/account/publishing/)
   - Click "Add a new pending publisher"

2. **Fill in Publisher Information**
   ```
   PyPI Project Name: parquetframe
   Owner: leechristophermurray
   Repository name: parquetframe
   Workflow filename: release.yml
   Environment name: release
   ```

3. **Save the Configuration**
   - Click "Add" to save the trusted publisher
   - This will show as "Pending" until the first successful publish

### 3. Repository Environment (Optional but Recommended)

1. **Go to Repository Settings**
   - Navigate to `https://github.com/leechristophermurray/parquetframe/settings/environments`

2. **Create Release Environment**
   - Click "New environment"
   - Name it `release`
   - Add protection rules if desired:
     - Required reviewers
     - Wait timer
     - Deployment branches (restrict to `main`)

### 4. Test the Setup

The trusted publishing will be tested automatically when you push a version tag:

```bash
git tag -a v0.2.1 -m "Test release"
git push origin v0.2.1
```

### 5. Verification

After the GitHub Action completes:

1. **Check PyPI**
   - Go to https://pypi.org/project/parquetframe/
   - Verify the new version is published

2. **Check Trusted Publisher Status**
   - Return to [Publishing Settings](https://pypi.org/manage/account/publishing/)
   - The publisher should now show as "Active" instead of "Pending"

## Troubleshooting

### Common Issues

1. **"Trusted publishing exchange token not found"**
   - Ensure the workflow filename matches exactly: `release.yml`
   - Check that the environment name is correct: `release`
   - Verify the repository owner and name are exact matches

2. **"Package validation failed"**
   - Check the package build logs in GitHub Actions
   - Ensure version numbers are consistent across files

3. **"Permission denied"**
   - Verify you have maintainer permissions on the PyPI project
   - Check that the GitHub repository settings allow Actions to run

### Support

If you encounter issues:

1. Check the [PyPI Trusted Publishing Documentation](https://docs.pypi.org/trusted-publishers/)
2. Review GitHub Actions logs for detailed error messages
3. Contact PyPI support if needed

## Security Benefits

✅ **No API Keys**: No secrets stored in GitHub repository
✅ **Automatic Rotation**: Tokens are short-lived and auto-generated
✅ **Audit Trail**: All publishing actions are logged and traceable
✅ **Fine-grained Control**: Restrict publishing to specific workflows and branches

## Next Steps

Once trusted publishing is configured:

1. The release process becomes fully automated
2. Simply push a version tag to trigger publishing
3. Monitor releases via GitHub Actions and PyPI project page
4. Update documentation as needed for new releases
