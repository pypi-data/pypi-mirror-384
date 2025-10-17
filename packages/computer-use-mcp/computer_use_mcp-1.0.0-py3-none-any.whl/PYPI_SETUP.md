# PyPI Publishing Setup Guide

This guide walks you through setting up automated PyPI publishing with GitHub Actions using **Trusted Publishers** (the most secure method - no API tokens needed!).

## Overview

This repository uses GitHub Actions to automatically publish to PyPI when you create a new release. It uses PyPI's **Trusted Publishers** feature for authentication, which is more secure than API tokens.

## Setup Steps

### 1. Configure PyPI Trusted Publisher

**Before creating your first release**, you need to register this GitHub repository as a trusted publisher on PyPI.

1. **Go to PyPI**: https://pypi.org/manage/account/publishing/

2. **Add a new pending publisher** with these exact details:
   - **PyPI Project Name:** `computer-use-mcp`
   - **Owner:** `vincenthopf`
   - **Repository name:** `computer-use-mcp`
   - **Workflow name:** `publish.yml`
   - **Environment name:** `pypi`

3. **Click "Add"**

**Important Notes:**
- Do this BEFORE your first release
- All fields must match exactly
- The project name will be claimed when you first publish
- No API tokens needed - GitHub OIDC handles authentication

### 2. Create a GitHub Environment

1. Go to your repository settings: https://github.com/vincenthopf/computer-use-mcp/settings/environments

2. Click **"New environment"**

3. Name it exactly: `pypi`

4. **(Optional but recommended)** Add protection rules:
   - ✅ Required reviewers: Add yourself
   - ✅ Wait timer: 0 minutes
   - ✅ Deployment branches: Only `main`

This adds an extra approval step before publishing to PyPI.

### 3. Verify Workflows are Enabled

1. Go to: https://github.com/vincenthopf/computer-use-mcp/actions

2. Ensure workflows are enabled (they should be automatically)

3. You should see two workflows:
   - **Tests** - Runs on every push/PR
   - **Publish to PyPI** - Runs on releases

## Publishing a New Version

### Method 1: GitHub Releases (Recommended)

This triggers the publish workflow automatically:

1. **Update version** in `pyproject.toml`:
   ```toml
   version = "1.0.1"  # Bump version
   ```

2. **Commit and push**:
   ```bash
   git add pyproject.toml
   git commit -m "chore: Bump version to 1.0.1"
   git push origin main
   ```

3. **Create a release on GitHub**:
   - Go to: https://github.com/vincenthopf/computer-use-mcp/releases/new
   - Tag: `v1.0.1` (must start with 'v')
   - Title: `v1.0.1 - Release Title`
   - Description: Copy from CHANGELOG.md
   - Click **"Publish release"**

4. **Watch the workflow**:
   - Go to Actions tab
   - Watch the "Publish to PyPI" workflow run
   - If you set up environment protection, approve the deployment

5. **Verify publication**:
   - Check: https://pypi.org/project/computer-use-mcp/

### Method 2: Manual Trigger

You can also manually trigger the publish workflow:

1. Go to: https://github.com/vincenthopf/computer-use-mcp/actions/workflows/publish.yml

2. Click **"Run workflow"**

3. Select branch: `main`

4. Click **"Run workflow"**

**Note:** This still requires PyPI Trusted Publisher to be configured.

## Security Best Practices

### ✅ What We're Using (Secure)

- **PyPI Trusted Publishers**: Uses OpenID Connect (OIDC) tokens
- **No API tokens**: Nothing to leak or expire
- **GitHub environment protection**: Requires approval before publishing
- **Minimal permissions**: Workflow only has `id-token: write` permission
- **Official actions**: Uses `pypa/gh-action-pypi-publish@release/v1`

### ❌ What We're NOT Using (Less Secure)

- ❌ PyPI API tokens stored as GitHub secrets
- ❌ Username/password authentication
- ❌ Manual publishing from local machine

## Workflows Overview

### `test.yml` - Continuous Integration

**Triggers:**
- Every push to `main`
- Every pull request
- Manual trigger

**What it does:**
- Tests on Python 3.10, 3.11, 3.12, 3.13
- Runs validation tests (`test_server.py`)
- Tests package build
- Checks Python syntax

**Badge:** ![Tests](https://github.com/vincenthopf/computer-use-mcp/actions/workflows/test.yml/badge.svg)

### `publish.yml` - PyPI Publishing

**Triggers:**
- New GitHub release
- Manual trigger

**What it does:**
- Checks out code
- Installs UV and dependencies
- Verifies package version
- Builds package with `uv build`
- Publishes to PyPI using Trusted Publishers

**Environment:** `pypi` (requires approval if protected)

## Troubleshooting

### Error: "Trusted publisher configuration mismatch"

**Cause:** PyPI Trusted Publisher settings don't match workflow.

**Fix:**
1. Go to: https://pypi.org/manage/account/publishing/
2. Verify all fields match exactly:
   - Repository: `vincenthopf/computer-use-mcp`
   - Workflow: `publish.yml`
   - Environment: `pypi`

### Error: "Environment protection rules not met"

**Cause:** Environment requires approval but wasn't provided.

**Fix:**
1. Go to Actions → Workflow run
2. Click **"Review deployments"**
3. Select `pypi` environment
4. Click **"Approve and deploy"**

### Error: "Project name already claimed"

**Cause:** Someone else published a package with this name.

**Fix:**
1. Choose a different package name
2. Update `pyproject.toml` → `name`
3. Update PyPI Trusted Publisher settings
4. Update README and documentation

## First-Time Publishing Checklist

Before publishing version 1.0.0:

- [ ] PyPI account created
- [ ] Trusted Publisher configured on PyPI
- [ ] GitHub environment `pypi` created
- [ ] Version is `1.0.0` in `pyproject.toml`
- [ ] CHANGELOG.md has release notes
- [ ] All tests passing locally
- [ ] README.md is up to date
- [ ] Package builds locally: `uv build`
- [ ] Create GitHub release `v1.0.0`
- [ ] Watch workflow complete
- [ ] Verify on PyPI: https://pypi.org/project/computer-use-mcp/

## Testing the Installation

After successful publication:

```bash
# Test installation
uvx computer-use-mcp --help

# Test in Claude Desktop
# Add to config and restart
```

## Resources

- **PyPI Trusted Publishers Guide**: https://docs.pypi.org/trusted-publishers/
- **GitHub OIDC**: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect
- **PyPI Publishing Action**: https://github.com/marketplace/actions/pypi-publish

## Support

If you encounter issues:

1. Check workflow logs in Actions tab
2. Verify PyPI Trusted Publisher configuration
3. Ensure all fields match exactly
4. Check GitHub environment protection rules
5. Open an issue if problems persist

---

**Remember:** The first publish must be done via GitHub Actions with Trusted Publishers configured. You cannot publish manually without setting up Trusted Publishers first.
