#!/usr/bin/env python3
"""
Script to copy files and folders from this repo to a remote repo and create requirements.txt
"""

import sys
import shutil
import argparse
from pathlib import Path
import re


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


def get_files_to_copy():
    """
    Define the list of files/folders to copy and their destination paths.
    Returns a list of tuples: (source_path, destination_path)
    """
    return [
        # Documentation and examples
        ("docs/examples", "docs/examples"),
        ("README.md", "README.md"),
        ("docs/PUBLIC_CHANGELOG.md", "CHANGELOG.md"),
        ("TROUBLESHOOTING.md", "TROUBLESHOOTING.md"),
        # Setup script
        ("setupEnvironment.ps1", "setupEnvironment.ps1"),
        ("public_release_scripts/.gitignore", ".gitignore"),
    ]


def clean_destination_repo(dest_repo):
    """
    Delete all contents of the destination repository except git-related files.
    Preserves: .git, .gitignore, .gitmodules, .gitattributes
    """
    dest_path = Path(dest_repo)

    if not dest_path.exists():
        print(f"Destination repo doesn't exist yet: {dest_path}")
        return [], []

    deleted_items = []
    failed_items = []

    try:
        # Get all items in the destination directory
        items = list(dest_path.iterdir())

        if not items:
            print("Destination repo is already empty")
            return [], []

        print(f"Cleaning destination repo: {dest_path}")

        for item in items:
            try:
                # Skip git-related files and folders to preserve repository history
                if item.name in [".git", ".gitignore", ".gitmodules", ".gitattributes"]:
                    print(f"⚠ Skipping {item.name} (preserving git configuration)")
                    continue

                if item.is_file():
                    item.unlink()
                    print(f"✓ Deleted file: {item.name}")
                    deleted_items.append(item.name)
                elif item.is_dir():
                    shutil.rmtree(item)
                    print(f"✓ Deleted folder: {item.name}")
                    deleted_items.append(item.name)
            except Exception as e:
                print(f"✗ Error deleting {item.name}: {e}")
                failed_items.append(item.name)

        if failed_items:
            print(f"⚠ Failed to delete {len(failed_items)} items: {failed_items}")

    except Exception as e:
        print(f"✗ Error accessing destination repo: {e}")
        failed_items.append(str(dest_path))

    return deleted_items, failed_items


def copy_files_and_folders(source_repo, dest_repo, files_to_copy):
    """Copy files and folders from source to destination repo"""
    source_path = Path(source_repo)
    dest_path = Path(dest_repo)

    # Create destination directory if it doesn't exist
    dest_path.mkdir(parents=True, exist_ok=True)

    copied_files = []
    failed_files = []

    for source_rel, dest_rel in files_to_copy:
        source_full = source_path / source_rel
        dest_full = dest_path / dest_rel

        try:
            if source_full.exists():
                # Create parent directories if they don't exist
                dest_full.parent.mkdir(parents=True, exist_ok=True)

                if source_full.is_file():
                    shutil.copy2(source_full, dest_full)
                    print(f"✓ Copied file: {source_rel} -> {dest_rel}")
                    copied_files.append(dest_rel)
                elif source_full.is_dir():
                    # Remove destination if it exists and copy the directory
                    if dest_full.exists():
                        shutil.rmtree(dest_full)
                    shutil.copytree(source_full, dest_full)
                    print(f"✓ Copied folder: {source_rel} -> {dest_rel}")
                    copied_files.append(dest_rel)
            else:
                print(f"⚠ Warning: Source path does not exist: {source_rel}")
                failed_files.append(source_rel)

        except Exception as e:
            print(f"✗ Error copying {source_rel}: {e}")
            failed_files.append(source_rel)

    return copied_files, failed_files


def create_requirements_txt(dest_repo, version):
    """Create requirements.txt file in the destination repo"""
    dest_path = Path(dest_repo)
    requirements_file = dest_path / "requirements.txt"

    try:
        with open(requirements_file, "w") as f:
            f.write(f"breathe_design >= {version}\n")

        print(f"✓ Created requirements.txt with breathe_design >= {version}")
        return True

    except Exception as e:
        print(f"✗ Error creating requirements.txt: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Copy files from this repo to a remote repo and create requirements.txt"
    )
    parser.add_argument(
        "repo_path",
        nargs="?",
        default="D:/Git/breathe_design_examples",
        help="Path to the destination repository (default: D:/Git/breathe_design_examples)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be copied without actually copying",
    )

    args = parser.parse_args()

    # Get current repo path (go up one level from public_release_scripts)
    current_repo = Path(__file__).parent.parent
    dest_repo = Path(args.repo_path)

    print(f"Source repo: {current_repo}")
    print(f"Destination repo: {dest_repo}")
    print()

    try:
        # Get version from __init__.py
        version = get_version_from_init()
        print(f"Found breathe_design version: {version}")
        print()

        # Get list of files to copy
        files_to_copy = get_files_to_copy()

        if args.dry_run:
            print("DRY RUN - What would happen:")
            print()

            # Show what would be deleted
            if dest_repo.exists():
                items = list(dest_repo.iterdir())
                if items:
                    print("Would DELETE all existing files/folders:")
                    git_files_found = []
                    git_protected_files = [
                        ".git",
                        ".gitignore",
                        ".gitmodules",
                        ".gitattributes",
                    ]

                    for item in items:
                        if item.name in git_protected_files:
                            git_files_found.append(item.name)
                            continue  # Skip git files in display
                        file_type = "folder" if item.is_dir() else "file"
                        print(f"  ✗ {item.name} ({file_type})")

                    if git_files_found:
                        print(
                            f"  ⚠ Git files would be PRESERVED: {', '.join(git_files_found)}"
                        )

                    if not any(item.name not in git_protected_files for item in items):
                        print("  (Only git-related files present - would be preserved)")
                else:
                    print("Destination repo is empty - nothing to delete")
            else:
                print("Destination repo doesn't exist yet - would create it")
            print()

            # Show what would be copied
            print("Would COPY these files:")
            for source_rel, dest_rel in files_to_copy:
                source_full = current_repo / source_rel
                if source_full.exists():
                    file_type = "folder" if source_full.is_dir() else "file"
                    print(f"  ✓ {source_rel} -> {dest_rel} ({file_type})")
                else:
                    print(f"  ⚠ {source_rel} -> {dest_rel} (MISSING)")
            print()
            print(f"Would CREATE requirements.txt with: breathe_design >= {version}")
            return

        # Clean destination repo first
        print("Cleaning destination repository...")
        deleted_items, delete_failed = clean_destination_repo(dest_repo)
        print()

        # Copy files and folders
        print("Copying files and folders...")
        copied_files, failed_files = copy_files_and_folders(
            current_repo, dest_repo, files_to_copy
        )
        print()

        # Create requirements.txt
        print("Creating requirements.txt...")
        requirements_success = create_requirements_txt(dest_repo, version)
        print()

        # Summary
        print("=" * 50)
        print("SUMMARY")
        print("=" * 50)
        print(f"Deleted {len(deleted_items)} existing items")
        if delete_failed:
            print(f"Failed to delete {len(delete_failed)} items: {delete_failed}")
        print(f"Successfully copied {len(copied_files)} items")
        if failed_files:
            print(f"Failed to copy {len(failed_files)} items: {failed_files}")
        print(f"Requirements.txt created: {'✓' if requirements_success else '✗'}")
        print(f"Destination: {dest_repo}")

    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
