import requests
from packaging.version import Version
import os

gitlab_token = os.getenv("GITLAB_TOKEN")
ci_api_v4_url = os.getenv("CI_API_V4_URL", default="https://gitlab.example.com/api/v4")
ci_project_id = os.getenv("CI_PROJECT_ID")


def fetch_tags():
    """Fetch all tags from the GitLab project."""
    headers = {"PRIVATE-TOKEN": gitlab_token}
    url = f"{ci_api_v4_url}/projects/{ci_project_id}/repository/tags"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def create_or_update_tag(tag_name, target):
    """Create or update a GitLab tag."""
    headers = {"PRIVATE-TOKEN": gitlab_token}
    tag_url = f"{ci_api_v4_url}/projects/{ci_project_id}/repository/tags/{tag_name}"

    # Check if the tag already exists
    response = requests.get(tag_url, headers=headers)
    if response.status_code == 200:
        # Delete the tag if it exists
        print(f"Tag '{tag_name}' exists. Deleting it...")
        delete_response = requests.delete(tag_url, headers=headers)
        delete_response.raise_for_status()

    # Create the new tag
    create_url = f"{ci_api_v4_url}/projects/{ci_project_id}/repository/tags"
    payload = {"tag_name": tag_name, "ref": target}
    create_response = requests.post(create_url, headers=headers, json=payload)
    create_response.raise_for_status()
    print(f"Tag '{tag_name}' created pointing to '{target}'.")


def update_alias_tags():
    """Update alias tags based on the latest semantic version tags."""
    tags = fetch_tags()
    semantic_tags = [
        tag["name"]
        for tag in tags
        if tag["name"].startswith("v") and tag["name"][1:].replace(".", "").isdigit()
    ]
    versions = sorted([Version(tag.lstrip("v")) for tag in semantic_tags], reverse=True)

    if not versions:
        raise ValueError("No semantic version tags found.")

    # Determine alias tags
    latest_version = versions[0]
    major_tag = f"v{latest_version.major}"
    minor_tag = f"v{latest_version.major}.{latest_version.minor}"

    print(f"Latest version: {latest_version}")
    print("Updating alias tags:")
    print(f"  {major_tag} -> {latest_version}")
    print(f"  {minor_tag} -> {latest_version}")

    # Update tags using the GitLab API
    create_or_update_tag(major_tag, f"v{latest_version}")
    create_or_update_tag(minor_tag, f"v{latest_version}")


if __name__ == "__main__":
    try:
        update_alias_tags()
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
