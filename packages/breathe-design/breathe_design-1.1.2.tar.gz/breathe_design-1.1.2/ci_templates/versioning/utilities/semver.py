import re
import os
import jira
import json
from jira import JIRAError
from breathe_utils import logging as breathe_logging
import logging
import argparse
import requests
import subprocess
import yaml

# Setup logger
_logger = logging.getLogger(__name__)

# Initialize globals
BREATHE_JIRA_URL = "https://breathe.atlassian.net/"
PROGRAM_DESCRIPTION = ""


def get_ticket_id(input_str: str) -> str:
    """Function to get the first JIRA ticket id from an input string

    Args:
        input_str (str): string to search for pattern

    Returns:
        str: Jira ticket ID
    """
    pattern = r"[A-Z]+-\d+"
    match = re.search(pattern, input_str)
    return match.group(0) if match else None


def get_version_increment_from_ticket(ticket_id: str) -> str:
    """Function to parse version increment from a Jira ticket

    Args:
        ticket_id (str): Jira ticket ID

    Returns:
        str: string of version increment
    """
    pattern = r"version:\s*(major|minor|patch)"
    user = os.getenv("JIRA_USER")
    token = os.getenv("JIRA_TOKEN")

    try:
        jira_instance = jira.JIRA(server=BREATHE_JIRA_URL, basic_auth=(user, token))
        issue = jira_instance.issue(ticket_id)
        description = issue.fields.description
        match = re.search(pattern, description, re.IGNORECASE)
        return match.group(1).lower() if match else "patch"
    except (JIRAError, Exception) as e:
        _logger.warning(f"Jira error: {e}")
        return "patch"


def get_version_increment_from_commit(commit_msg: str) -> str:
    """Function to parse version increment from a commit message

    Args:
        commit_msg (str): string input of commit message

    Returns:
        str: version increment
    """
    pattern = r"bump\s*(major|minor|patch)"
    match = re.search(pattern, commit_msg, re.IGNORECASE)
    return match.group(1).lower() if match else "patch"


def get_release(ticket_id: str) -> str:
    """Function to get first fixVersion from Jira ticket

    Args:
        ticket_id (str): jira ticket id

    Returns:
        str: jira release
    """
    user = os.getenv("JIRA_USER")
    token = os.getenv("JIRA_TOKEN")

    try:
        jira_instance = jira.JIRA(server=BREATHE_JIRA_URL, basic_auth=(user, token))
        issue = jira_instance.issue(ticket_id)
        versions = issue.fields.fixVersions
        return versions[0].name if versions else None
    except JIRAError as e:
        _logger.error(f"Jira error: {e}")
        exit(1)


def calculate_new_tag(current_tag: str, version_increment: str) -> str:
    """Function to calculate new version from current version and increment

    Args:
        current_tag (str): current semantic version (prefixed with v)
        version_increment (str): semantic version increment

    Returns:
        str: incremented version
    """
    current_tag = current_tag.lstrip("v")
    major, minor, patch = map(int, current_tag.split("."))

    if version_increment == "major":
        major += 1
        minor = 0
        patch = 0
    elif version_increment == "minor":
        minor += 1
        patch = 0
    elif version_increment == "patch":
        patch += 1

    return f"v{major}.{minor}.{patch}"


def create_git_tag(tag_name: str, ref: str, dry_run: bool = False):
    """Create a git tag using GitLab API

    Args:
        tag_name (str): version to tag
        ref (str): git ref to tag
        dry_run (bool, optional): flag to test api call. Defaults to False.

    Returns:
        dict or str: API response
    """
    gitlab_token = os.getenv("GITLAB_TOKEN")
    ci_api_v4_url = os.getenv(
        "CI_API_V4_URL", default="https://gitlab.example.com/api/v4"
    )
    ci_project_id = os.getenv("CI_PROJECT_ID")

    url = f"{ci_api_v4_url}/projects/{ci_project_id}/repository/tags"
    headers = {"PRIVATE-TOKEN": gitlab_token}
    data = {"tag_name": tag_name, "ref": ref}
    if not dry_run:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 201:
            return response.json()
        return response.text
    else:
        print(data)


def write_version_to_txt(tag, dry_run=False):
    """Write version to a text file

    Args:
        tag (str): version tag
        dry_run (bool, optional): flag to test writing. Defaults to False.
    """
    if not dry_run:
        tag = tag.lstrip("v")
        with open("version", "w") as f:
            f.write("VERSION=" + str(tag))


def get_version_py():
    """Get version using hatch

    Returns:
        str: version
    """
    try:
        result = subprocess.run(
            ["hatch", "version"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        _logger.error(f"Error: {e}")
        return None


def get_version_yaml(yaml_file: str = "version.yaml"):
    """Get version from YAML file

    Args:
        yaml_file (str): path to YAML file

    Returns:
        str: version
    """
    with open(yaml_file, "r") as f:
        version_yaml = yaml.load(f, Loader=yaml.Loader)
    if "Suffix" in version_yaml:
        if (
            version_yaml["Suffix"] != ""
            and version_yaml["Suffix"] is not None
            and isinstance(version_yaml["Suffix"], str)
        ):
            return f"{version_yaml['Major']}.{version_yaml['Minor']}.{version_yaml['Patch']}_{version_yaml['Suffix']}"
        else:
            return f"{version_yaml['Major']}.{version_yaml['Minor']}.{version_yaml['Patch']}"
    else:
        return (
            f"{version_yaml['Major']}.{version_yaml['Minor']}.{version_yaml['Patch']}"
        )


def get_version_json(json_file: str = "package.json"):
    """Get version from JSON file

    Args:

    """
    with open(json_file, "r") as f:
        version_json = json.load(f)
    if "version" in version_json:
        return version_json["version"]
    else:
        _logger.error("Version not found in JSON file")
        exit(1)


def parse_version(version: str):
    """Parse a version string into its components

    Args:
        version (str): The version string

    Returns:
        tuple: Parsed version components (major, minor, patch, suffix)
    """
    pattern = r"(\d+)\.(\d+)\.(\d+)(?:[.-](dev|b\d+))?"
    match = re.match(pattern, version)
    if not match:
        _logger.error("Invalid version format")
        exit(1)
    major, minor, patch, suffix = match.groups()
    return int(major), int(minor), int(patch), suffix


def validate_version_increment(version, current_tag):
    """Validate the increment semantic version against the current version.

    Args:
        version (str): The version to be validated.
        current_tag (str): The current version.

    Returns:
        None
    """
    current_tag = current_tag.lstrip("v")
    inc_major, inc_minor, inc_patch, inc_suffix = parse_version(version)
    cur_major, cur_minor, cur_patch, cur_suffix = parse_version(current_tag)

    valid = False
    if inc_major == cur_major + 1 and inc_minor == 0 and inc_patch == 0:
        valid = True
    elif inc_major == cur_major and inc_minor == cur_minor + 1 and inc_patch == 0:
        valid = True
    elif (
        inc_major == cur_major and inc_minor == cur_minor and inc_patch == cur_patch + 1
    ):
        valid = True
    elif inc_suffix and cur_suffix:
        if inc_suffix.startswith("dev") and cur_suffix.startswith("dev"):
            valid = True
        elif inc_suffix.startswith("b") and cur_suffix.startswith("b"):
            valid = True

    if valid:
        _logger.info(f"Valid version increment: {version}")
    elif "Draft:" in os.getenv("CI_MERGE_REQUEST_TITLE"):
        _logger.info("Validation bypassed")
    else:
        valid_major = f"{cur_major + 1}.0.0"
        valid_minor = f"{cur_major}.{cur_minor + 1}.0"
        valid_patch = f"{cur_major}.{cur_minor}.{cur_patch + 1}"
        _logger.info(
            f"Invalid increment version, valid increments are: \n"
            f"major: {valid_major}\n"
            f"minor: {valid_minor}\n"
            f"patch: {valid_patch}"
        )
        exit(1)


def main():
    """Main function to parse arguments and execute versioning logic"""
    breathe_logging.setup_logging("log.log", append=False)
    parser = argparse.ArgumentParser(prog="semver", description=PROGRAM_DESCRIPTION)
    parser.add_argument("current_tag", help="Latest tag on current branch")
    parser.add_argument("pattern", help="pattern to search for JIRA ticket")
    parser.add_argument("commit_sha", help="Commit sha")
    parser.add_argument(
        "--dry_run", dest="dry_run", action="store_true", help="Flag to not update Jira"
    )
    args = parser.parse_args()

    ticket_id = get_ticket_id(args.pattern)
    _logger.info(f"Current tag {args.current_tag}")

    tagging_method = os.getenv("TAGGING_METHOD")
    if tagging_method == "ticket":
        version_increment = get_version_increment_from_ticket(ticket_id)
        tag = calculate_new_tag(args.current_tag, version_increment)
    elif tagging_method == "releases":
        release = get_release(ticket_id)
        tag = "v" + release
    elif tagging_method == "lite":
        version_increment = get_version_increment_from_commit(args.pattern)
        tag = calculate_new_tag(args.current_tag, version_increment)
    elif tagging_method == "python":
        version = get_version_py()
        validate_version_increment(version, args.current_tag)
        tag = "v" + version
    elif tagging_method == "yaml":
        yaml_file = os.getenv("YAML_VERSION_PATH", "version.yaml")
        _logger.info(f"Loading version from YAML file: {yaml_file}")
        version = get_version_yaml(yaml_file)
        current_tag = args.current_tag.split("_")[0]
        validate_version_increment(version, current_tag)
        tag = "v" + version
    elif tagging_method == "json":
        json_file = os.getenv("JSON_VERSION_PATH", "package.json")
        _logger.info(f"Loading version from JSON file: {json_file}")
        version = get_version_json(json_file)
        validate_version_increment(version, args.current_tag)
        tag = "v" + version
    else:
        version_increment = get_version_increment_from_commit(args.pattern)
        tag = calculate_new_tag(args.current_tag, version_increment)

    create_git_tag(tag, args.commit_sha, dry_run=args.dry_run)
    write_version_to_txt(tag, dry_run=args.dry_run)


main()
