# GitLab CI/CD Setup for Automated Releases

This document explains how to set up GitLab CI/CD to automatically create public releases.

## Overview

The `.gitlab-ci.yml` file includes a `create_public_release` job that:
- Runs manually on merge requests (temporary - for testing)
- Runs manually on merges to main branch
- Creates a release branch in the public repository
- Copies files and creates merge requests automatically

## Required Setup

### 1. Create a Project Access Token

The CI/CD job needs a GitLab access token to create merge requests in the public repository.

1. Go to your GitLab project → **Settings** → **Access Tokens**
2. Click **Add new token**
3. Configure the token:
   - **Token name**: `Release Automation`
   - **Expiration date**: Set a future date (e.g., 1 year)
   - **Role**: `Developer` or `Maintainer`
   - **Scopes**: Check `api` (required for creating merge requests)
4. Click **Create project access token**
5. **Copy the token immediately** (you won't see it again!)

### 2. Add CI/CD Variable

1. Go to your GitLab project → **Settings** → **CI/CD**
2. Expand **Variables** section
3. Click **Add variable**
4. Configure the variable:
   - **Key**: `GITLAB_RELEASE_TOKEN`
   - **Value**: The token you copied above
   - **Type**: `Variable`
   - **Environment scope**: `All`
   - **Protect variable**: ✅ (checked)
   - **Mask variable**: ✅ (checked)
   - **Expand variable reference**: ❌ (unchecked)
5. Click **Add variable**

### 3. Verify Submodule Configuration

Ensure the `public_release` submodule is properly configured in your repository:

```bash
# Check submodule status
git submodule status

# If needed, initialize submodule
git submodule init
git submodule update
```

## Usage

### Running the Release Job

The `create_public_release` job is configured as **manual** to prevent accidental releases.

#### On Merge Requests (Testing)
1. Create a merge request
2. Go to **CI/CD** → **Pipelines**
3. Click on the pipeline for your MR
4. Find the `create_public_release` job
5. Click the **play button** (▶️) to run it manually

#### On Main Branch (Production)
1. After merging to main
2. Go to **CI/CD** → **Pipelines**
3. Click on the latest pipeline
4. Find the `create_public_release` job
5. Click the **play button** (▶️) to run it manually

### What the Job Does

1. **Setup Environment**:
   - Installs required Python packages (`requests`)
   - Initializes and updates the `public_release` submodule
   - Configures git with CI user information

2. **Extract Release Info**:
   - Gets version from `breathe_design/__init__.py`
   - Gets current commit hash
   - Displays release information

3. **Run Release Process**:
   - Executes `create_public_release.py` script
   - Creates release branch: `release_{version}_{commit_hash}`
   - Copies files to public repository
   - Creates merge request (if token available)

### Expected Output

```
Creating public release for version 0.5.9 from commit bbd9d87
Target submodule: public_release
GitLab token available. Creating release with merge request.
Pulling latest changes from main in submodule...
✓ Successfully pulled latest main
Creating release branch: release_0.5.9_bbd9d87
✓ Created and switched to branch: release_0.5.9_bbd9d87
Running copy script to sync files...
[... file copying output ...]
✓ Files copied successfully
Committing changes in submodule...
✓ Committed changes: Release 0.5.9 from commit bbd9d87
Pushing branch release_0.5.9_bbd9d87 to origin...
✓ Pushed branch release_0.5.9_bbd9d87
Creating merge request...
Creating MR at: https://gitlab.com/api/v4/projects/.../merge_requests
From: release_0.5.9_bbd9d87 → main
✓ Merge request created successfully!
  URL: https://gitlab.com/.../merge_requests/1
  MR !1: Release 0.5.9 from commit bbd9d87
Release process completed successfully!
```

## Troubleshooting

### "GITLAB_TOKEN not set"
- The job will still run but skip merge request creation
- Follow steps above to create and configure the access token

### "Submodule not found"
- Ensure the `public_release` submodule is properly initialized
- Check that the submodule URL is correct in `.gitmodules`

### "Permission denied" errors
- Verify the access token has `api` scope
- Ensure the token user has Developer/Maintainer role
- Check that the token hasn't expired

### Job timeout
- The job has a 30-minute timeout
- Large file copies or network issues might cause timeouts
- Check the GitLab runner connectivity

## Future Changes

Currently, the job runs on both merge requests and main branch merges. In the future:

1. **Remove MR trigger**: Delete lines 84-86 in `.gitlab-ci.yml`
2. **Keep only main branch**: Keep lines 87-90 for production releases
3. **Consider automation**: Change `when: manual` to `when: on_success` for automatic releases

## Security Notes

- Access tokens should be treated as passwords
- Use masked variables to prevent token exposure in logs
- Set expiration dates on tokens
- Rotate tokens periodically
- Only grant minimum required permissions (`api` scope)
