#!/usr/bin/env python3
"""
Script to create a public release by:
1. Cloning the GitHub repository into public_repo folder
2. Pulling latest from main in the cloned repo
3. Creating a release branch with version and commit hash
4. Copying files from this repo to the cloned repo
5. Committing changes and creating a pull request
"""

import subprocess
import sys
import argparse
from pathlib import Path
import re
import requests
import os
import shutil


def run_command(cmd, cwd=None, capture_output=True):
    """Run a shell command and return the result"""
    try:
        if isinstance(cmd, str):
            cmd = cmd.split()

        result = subprocess.run(
            cmd, cwd=cwd, capture_output=capture_output, text=True, check=True
        )
        return result.stdout.strip() if capture_output else ""
    except subprocess.CalledProcessError as e:
        print(f"✗ Command failed: {' '.join(cmd)}")
        print(f"Error: {e.stderr if e.stderr else e}")
        raise


def get_version_from_init():
    """Extract version from breathe_design/__init__.py"""
    init_file = Path(__file__).parent.parent / "breathe_design" / "__init__.py"

    if not init_file.exists():
        raise FileNotFoundError(f"Could not find __init__.py at {init_file}")

    with open(init_file, "r") as f:
        content = f.read()

    # Look for __version__ = "x.y.z" pattern
    version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not version_match:
        raise ValueError("Could not find __version__ in __init__.py")

    return version_match.group(1)


def get_current_commit_hash():
    """Get the current commit hash of this repo"""
    return run_command("git rev-parse --short HEAD")


def get_current_branch():
    """Get the current branch name of this repo"""
    return run_command("git rev-parse --abbrev-ref HEAD")


def clone_github_repo(github_url, target_path):
    """Clone the GitHub repository into the target path"""
    print(f"Cloning GitHub repository: {github_url}")

    # Remove existing directory if it exists
    if target_path.exists():
        print(f"Removing existing directory: {target_path}")
        shutil.rmtree(target_path)

    # Clone the repository
    run_command(f"git clone {github_url} {target_path}")
    print(f"✓ Successfully cloned repository to {target_path}")


def pull_latest_main(repo_path):
    """Pull the latest changes from main branch in the cloned repo"""
    print("Pulling latest changes from main in cloned repo...")

    # Change to repo directory and pull latest main
    run_command("git checkout main", cwd=repo_path)
    run_command("git pull origin main", cwd=repo_path)

    print("✓ Successfully pulled latest main")


def create_release_branch(repo_path, version, commit_hash, source_branch):
    """Create a new release branch in the cloned repo"""
    branch_name = f"release_from_branch_{source_branch}_{version}_{commit_hash}"

    print(f"Creating release branch: {branch_name}")

    # Create and checkout new branch
    run_command(f"git checkout -b {branch_name}", cwd=repo_path)

    print(f"✓ Created and switched to branch: {branch_name}")
    return branch_name


def run_copy_script(repo_path):
    """Run the copy script to sync files to the cloned repo"""
    print("Running copy script to sync files...")

    # Run the copy script with the repo path as destination
    copy_script = Path(__file__).parent / "copy_to_remote_repo.py"
    run_command(f"python {copy_script} {repo_path}", capture_output=False)

    print("✓ Files copied successfully")


def commit_changes(repo_path, version, commit_hash):
    """Add all changes and commit them in the cloned repo"""
    print("Committing changes in cloned repo...")

    # Add all changes
    run_command(["git", "add", "."], cwd=repo_path)

    # Check if there are any changes to commit
    try:
        status = run_command("git status --porcelain", cwd=repo_path)
        if not status.strip():
            print("⚠ No changes to commit")
            return False
    except subprocess.CalledProcessError:
        pass

    # Commit changes
    commit_message = f"Release {version} from commit {commit_hash}"
    run_command(["git", "commit", "-m", commit_message], cwd=repo_path)

    print(f"✓ Committed changes: {commit_message}")
    return True


def push_branch(repo_path, branch_name):
    """Push the release branch to origin"""
    print(f"Pushing branch {branch_name} to origin...")

    try:
        run_command(f"git push -u origin {branch_name}", cwd=repo_path)
        print(f"✓ Pushed branch {branch_name}")
        return True
    except subprocess.CalledProcessError as e:
        if "403" in str(e) or "not allowed to push" in str(e).lower():
            print("✗ Push failed: Permission denied")
            print(
                "This usually means the CI job doesn't have write access to the GitHub repository."
            )
            print("Solutions:")
            print("1. Create a Personal Access Token with 'repo' scope")
            print("2. Set GITHUB_TOKEN as a CI/CD variable")
            print(f"3. The branch '{branch_name}' was created locally but not pushed")
            return False
        else:
            raise


def get_github_token():
    """Get GitHub access token from environment or user input"""
    # Try to get token from environment variable
    token = os.getenv("GITHUB_TOKEN")
    if token:
        return token

    # Try to get token from git config (if set)
    try:
        token = run_command("git config --global github.token")
        if token:
            return token
    except subprocess.CalledProcessError:
        pass

    # Ask user for token
    print("GitHub access token required for creating pull requests.")
    print("You can:")
    print("1. Set GITHUB_TOKEN environment variable")
    print("2. Set git config: git config --global github.token YOUR_TOKEN")
    print("3. Get a token from: https://github.com/settings/tokens")
    print("   (Needs 'repo' scope)")
    print()

    token = input("Enter your GitHub access token (or press Enter to skip): ").strip()
    return token if token else None


def create_pull_request(github_url, branch_name, version, commit_hash):
    """Create a pull request using GitHub REST API"""
    print("Creating pull request...")

    # Get access token
    token = get_github_token()
    if not token:
        print("⚠ No GitHub token provided. Please create pull request manually:")
        print("  1. Go to the GitHub repository")
        print(f"  2. Create a pull request from branch '{branch_name}' to 'main'")
        print(f"  3. Title: 'Release {version} from commit {commit_hash}'")
        print(f"  4. Description: Release of breathe_design version {version}")
        return False

    try:
        # Prepare pull request data
        title = f"Release {version} from commit {commit_hash}"
        description = f"""Release of breathe_design version {version} from source commit {commit_hash}.

This release includes:
- Updated documentation and examples
- Latest version of requirements.txt
- All necessary files for public distribution

Auto-generated by create_public_release.py"""

        # GitHub API endpoint
        match = re.match(r".*github.com/(.+\/.+)\.git", github_url)
        if not match:
            print(
                f"✗ Could not extract GitHub repository information from {github_url}"
            )
            return False
        repo_path_str = match.group(1)
        api_url = f"https://api.github.com/repos/{repo_path_str}/pulls"

        # Request payload
        payload = {
            "title": title,
            "head": branch_name,
            "base": "main",
            "body": description,
        }

        # Request headers
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

        print(f"Creating PR at: {api_url}")
        print(f"From: {branch_name} → main")

        # Make the API request
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)

        if response.status_code == 201:
            pr_data = response.json()
            pr_url = pr_data.get("html_url", "")
            pr_number = pr_data.get("number", "")
            print("✓ Pull request created successfully!")
            print(f"  URL: {pr_url}")
            print(f"  PR #{pr_number}: {title}")
            return True
        else:
            print(f"✗ Failed to create pull request (HTTP {response.status_code})")
            try:
                error_info = response.json()
                if "message" in error_info:
                    print(f"  Error: {error_info['message']}")
                if "errors" in error_info:
                    for error in error_info["errors"]:
                        print(f"  Details: {error}")
            except ValueError:
                print(f"  Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"✗ Network error creating pull request: {e}")
        return False
    except Exception as e:
        print(f"✗ Error creating pull request: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Create a public release in the GitHub repository"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )
    parser.add_argument(
        "--skip-pr",
        action="store_true",
        help="Skip creating the pull request",
    )
    parser.add_argument(
        "--skip-manual-review",
        action="store_true",
        help="Skip manual review step and proceed automatically (useful for CI/CD)",
    )

    args = parser.parse_args()

    # Get paths
    current_repo = Path(
        __file__
    ).parent.parent  # Go up one level from public_release_scripts
    github_repo_path = current_repo / "public_repo"

    # GitHub repository URL
    github_url = os.environ["GITHUB_REPO"]

    try:
        # Get version, commit info, and source branch
        version = get_version_from_init()
        commit_hash = get_current_commit_hash()
        source_branch = get_current_branch()

        print(f"Source repo: {current_repo}")
        print(f"GitHub repo: {github_url}")
        print(f"Target path: {github_repo_path}")
        print(f"Version: {version}")
        print(f"Commit hash: {commit_hash}")
        print(f"Source branch: {source_branch}")
        print()

        if args.dry_run:
            print("DRY RUN - What would happen:")
            print("1. Clone GitHub repository")
            print("2. Pull latest main in cloned repo")
            print(
                f"3. Create branch: release_from_branch_{source_branch}_{version}_{commit_hash}"
            )
            print("4. Run copy script to sync files")
            print("5. Commit all changes")
            print("6. Push branch to origin")
            if not args.skip_pr:
                print("7. Create pull request")
            return

        # Step 1: Clone GitHub repository
        clone_github_repo(github_url, github_repo_path)
        print()

        # Step 2: Pull latest main
        pull_latest_main(github_repo_path)
        print()

        # Step 3: Create release branch
        branch_name = create_release_branch(
            github_repo_path, version, commit_hash, source_branch
        )
        print()

        # Step 4: Run copy script
        run_copy_script(github_repo_path)
        print()

        # Step 4.5: Allow user to inspect and modify working tree before committing
        if not args.skip_manual_review:
            print("=" * 60)
            print("INSPECT AND MODIFY WORKING TREE")
            print("=" * 60)
            print(f"Release branch: {branch_name}")
            print(f"Local repository path: {github_repo_path}")
            print()
            print("You can now inspect and modify the working tree before committing.")
            print("You can:")
            print(f"1. Check git status: cd {github_repo_path} && git status")
            print(f"2. Review changes: cd {github_repo_path} && git diff")
            print(f"3. Check branch: cd {github_repo_path} && git branch -v")
            print(f"4. Modify files as needed in: {github_repo_path}")
            print(f"5. Add/remove files: cd {github_repo_path} && git add/rm <files>")
            print()

            input(
                "Press Enter to continue with committing changes (or Ctrl+C to cancel)..."
            )
            print()
        else:
            print("Skipping manual review step (--skip-manual-review flag provided)")
            print()

        # Step 5: Commit changes
        has_changes = commit_changes(github_repo_path, version, commit_hash)
        if not has_changes:
            print("No changes to release. Exiting.")
            return
        print()

        # Step 6: Push branch
        push_success = push_branch(github_repo_path, branch_name)
        if not push_success:
            print(
                "⚠ Branch push failed. Release branch was created locally but not pushed to remote."
            )
            print(
                "You may need to push manually or fix the authentication configuration."
            )
        print()

        # Step 7: Create pull request (if not skipped and push was successful)
        if not args.skip_pr and push_success:
            pr_success = create_pull_request(
                github_url, branch_name, version, commit_hash
            )
            if not pr_success:
                print(
                    "⚠ Pull request creation failed, but release branch was created successfully"
                )
        elif not args.skip_pr and not push_success:
            print("⚠ Skipping pull request creation due to push failure")

        # Summary
        print("=" * 60)
        print("RELEASE SUMMARY")
        print("=" * 60)
        print(f"Version: {version}")
        print(f"Source commit: {commit_hash}")
        print(f"Release branch: {branch_name}")
        print(
            f"Branch pushed: {'✓' if push_success else '✗ (failed - check permissions)'}"
        )
        print(f"GitHub repo: {github_url}")
        print(f"Local path: {github_repo_path}")

    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
