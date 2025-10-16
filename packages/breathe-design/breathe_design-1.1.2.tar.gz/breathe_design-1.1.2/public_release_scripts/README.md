# Public Release Scripts

This folder contains scripts to automate the creation of public releases for the breathe_design library.

## Files Overview

- **`copy_to_remote_repo.py`** - Copies files from this repo to a target repository
- **`create_public_release.py`** - Complete release automation (pulls, branches, copies, commits, creates MR)
- **`setupEnvironment.ps1`** - PowerShell script that gets copied to release repos for easy setup
- **`GITLAB_SETUP.md`** - Instructions for setting up GitLab API authentication
- **`GITLAB_CI_SETUP.md`** - Instructions for setting up automated releases via GitLab CI/CD
- **`README.md`** - This file

## Quick Start

### 1. One-time Setup
- Follow instructions in `GITLAB_SETUP.md` to set up GitLab API access
- Follow instructions in `GITLAB_CI_SETUP.md` to set up automated CI/CD releases
- Ensure the `public_release` submodule is initialized

### 2. Create a Release

#### Option A: Manual (Local)
```bash
# Preview what would happen
python public_release_scripts/create_public_release.py --dry-run

# Create actual release
python public_release_scripts/create_public_release.py
```

#### Option B: Automated (GitLab CI/CD)
1. Push changes to main branch or create a merge request
2. Go to **CI/CD** → **Pipelines** in GitLab
3. Find the `create_public_release` job
4. Click the **play button** (▶️) to trigger the release manually
5. The job will automatically create the release and merge request

### 3. What Gets Released
The following files/folders are copied to the public repository:
- `docs/examples/` → `examples/`
- `docs/installation.md` → `docs/installation.md`
- `docs/create_a_sim.md` → `docs/create_a_sim.md`
- `README.md` → `README.md`
- `CHANGELOG.md` → `CHANGELOG.md`
- `TROUBLESHOOTING.md` → `TROUBLESHOOTING.md`
- `setupEnvironment.ps1` → `setupEnvironment.ps1`
- `requirements.txt` (auto-generated with current version)

## Individual Script Usage

### Copy Script Only
```bash
# Copy to default location (D:/Git/breathe_design_examples)
python public_release_scripts/copy_to_remote_repo.py

# Copy to custom location
python public_release_scripts/copy_to_remote_repo.py "C:/path/to/target/repo"

# Preview what would be copied
python public_release_scripts/copy_to_remote_repo.py --dry-run
```

### Release Script Options
```bash
# Full release process
python public_release_scripts/create_public_release.py

# Skip merge request creation
python public_release_scripts/create_public_release.py --skip-mr

# Preview the entire process
python public_release_scripts/create_public_release.py --dry-run
```

## Setup Script for End Users

The `setupEnvironment.ps1` script is included in each release to help users set up their environment:

```powershell
# In the released repository, users can run:
.\setupEnvironment.ps1
```

This script will:
- Check Python version (requires 3.11+)
- Create a virtual environment in `venv/`
- Install requirements from `requirements.txt`
- Provide activation instructions

## Release Process Overview

1. **Pull latest main** in the submodule
2. **Create release branch** named `release_{version}_{commit_hash}`
3. **Clean destination** (delete all existing files)
4. **Copy files** from source to submodule
5. **Generate requirements.txt** with current version
6. **Commit changes** with descriptive message
7. **Push branch** to GitLab
8. **Create merge request** via GitLab API

## Troubleshooting

- **"public_release submodule not found"**: Make sure the submodule is properly initialized
- **"Could not find __init__.py"**: Ensure you're running from the repository root
- **GitLab API errors**: Check `GITLAB_SETUP.md` for authentication setup
- **Path issues**: Scripts expect to be run from the repository root directory
