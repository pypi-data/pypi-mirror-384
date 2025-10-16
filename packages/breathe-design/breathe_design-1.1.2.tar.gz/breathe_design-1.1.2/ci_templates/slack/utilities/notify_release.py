import os
from slack_sdk import WebClient
import re
import logging
from breathe_utils import logging as breathe_logging

channel = os.getenv("SLACK_CHANNEL")
token = os.getenv("SLACK_TOKEN")

breathe_logging.setup_logging("log.log", append=False)
_logger = logging.getLogger(__name__)

# Read the changelog file
try:
    with open("CHANGELOG.md", "r") as file:
        changelog_content = file.read()
except:  # noqa: E722
    try:
        with open("Changelog.md", "r") as file:
            changelog_content = file.read()
    except:  # noqa: E722
        _logger.error("No changelog file found")


# Define the pattern to match release entries
pattern = r"## \[(.*?)\] - (\d{2}/\d{2}/\d{4})\n(.*?)(?=\s*## \[|\Z)"

# Find all release entries
matches = re.findall(pattern, changelog_content, re.DOTALL)

if matches:
    # Get the latest release
    latest_release = matches[0]
    version = latest_release[0]
    date = latest_release[1]
    changes = latest_release[2].strip()

    ci_project_name = os.getenv("CI_PROJECT_TITLE")

    # Format the details into a Slack message
    slack_message = f"New Release of {ci_project_name} (v{version}):\n\n{changes}"

    # Send the Slack message or print it for testing
    print(slack_message)
else:
    print("No releases found in the changelog.")


# Set up a WebClient with the Slack OAuth token
client = WebClient(token=token)

# Send a message
client.chat_postMessage(channel=channel, text=slack_message, username="Breathe DevOps")
