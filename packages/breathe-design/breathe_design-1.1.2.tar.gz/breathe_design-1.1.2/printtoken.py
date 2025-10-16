import os

os.environ["API_URL"] = (
    "https://breathe-platform-backend-service-dev.azurewebsites.net/api/v1"
)

from breathe_design.api_interface import api_interface as api

api._auth.logout()
api.ensure_logged_in()
print(api._auth.get_token())
