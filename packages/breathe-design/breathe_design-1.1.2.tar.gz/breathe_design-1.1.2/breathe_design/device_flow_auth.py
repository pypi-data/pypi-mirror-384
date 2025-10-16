import time
import json
import logging
import requests
import webbrowser
import tempfile
import os
import datetime
from threading import Lock
from . import __version__

_logger = logging.getLogger(__name__)

temp_dir = tempfile.mkdtemp(prefix="myapp_")


class _DeviceFlowAuth:
    """Don't create an instance of this class, use the [device_auth] instance in this module."""

    def __init__(self, poll_interval=5):
        """
        Manages authentication using OAuth 2.0 Device Flow.

        :param poll_interval: How often to poll for token (in seconds).
        """

        self._poll_interval = poll_interval
        self._device_code_data: dict[str, str] | None = None
        self._token_data: dict[str, str] | None = None
        self._lock = Lock()
        self._last_time_token_checked = datetime.datetime.min

        tmp_dir_name = "devtmp"
        tmp_token_file = "dfile"
        self._tmp_dir_path = os.path.join(tempfile.gettempdir(), tmp_dir_name)
        self._tmp_token_file_path = os.path.join(self._tmp_dir_path, tmp_token_file)

        self._try_load_token_from_tmp()

        if "API_URL" in os.environ:
            self._api_url = os.environ["API_URL"]
            _logger.info(f"API_URL set from environment to {self._api_url}")
        else:
            self._api_url = (
                "https://bbt-apim-platform-prod.azure-api.net/platform/api/v1"
            )

    def _try_load_token_from_tmp(self):
        """Try to load the token from a temporary file

        Returns:
            _type_: _description_
        """
        if not os.path.exists(self._tmp_dir_path):
            return False

        if not os.path.exists(self._tmp_token_file_path):
            return False

        try:
            with open(self._tmp_token_file_path, "r") as f:
                token_data = json.load(f)
                self._token_data = token_data
                return True
        except:  # noqa E722
            return False

    def _save_token_to_tmp(self):
        """Saves the token to a temporary file."""
        if self._token_data is None:
            return

        if not os.path.exists(self._tmp_dir_path):
            os.makedirs(self._tmp_dir_path)

        with open(self._tmp_token_file_path, "w") as f:
            json.dump(self._token_data, f)

    def _delete_tmp_token_file(self):
        if os.path.exists(self._tmp_token_file_path):
            os.remove(self._tmp_token_file_path)

    def _make_http_request(
        self,
        method,
        endpoint,
        payload: dict | None = None,
        headers=None,
    ):
        """Helper function to make HTTP requests using http.client."""

        response = requests.post(
            f"{self._api_url}{endpoint}", json=payload, headers=headers
        )
        return response

    def _get_device_code(self):
        """Requests a device code for user authentication."""
        response = self._make_http_request("POST", "/device-auth/code")
        if response.status_code != 200:
            print(f"⚠️ Failed to log in! {response.status_code}")
            return False

        response_data = response.json()
        self._device_code_data = response_data
        self._poll_interval = response_data["interval"]

        print(
            f"\n🚀 Open this URL in a browser and verify the code shown is {response_data['user_code']}"
        )
        verification_uri = response_data["verification_uri_complete"]
        print(f"🔗 {verification_uri}")
        webbrowser.open_new_tab(verification_uri)
        return True

    def _poll_for_token(self):
        """Polls the token endpoint until the user authorizes the device."""
        print("\n⏳ Waiting for user authorization...")
        device_code = self._device_code_data["device_code"]
        timeout_time = datetime.datetime.now() + datetime.timedelta(seconds=60)
        while True:
            try:
                response = self._make_http_request(
                    "POST",
                    "/device-auth/poll",
                    payload={"device_code": device_code},
                )

                response_data = response.json()
                if response.status_code == 200:
                    self._token_data = response_data
                    self._save_token_to_tmp()
                    print("\n✅ Authentication successful!")
                    return True
                    break
                elif response_data.get("error") == "authorization_pending":
                    time.sleep(self._poll_interval)  # Wait before polling again
                elif response_data.get("error") == "slow_down":
                    self._poll_interval += 5  # Adjust polling interval if required
                    time.sleep(self._poll_interval)
                else:
                    raise Exception(
                        f"⚠️ Authentication failed: {response_data.get('error_description', 'Unknown error')}"
                    )
            except Exception as e:
                error_message = e.args[0]  # Get the error message string

                # Find the position of `{` (start of JSON) and extract only the JSON part
                json_start = error_message.find("{")
                if json_start != -1:
                    try:
                        error_json = json.loads(
                            error_message[json_start:]
                        )  # Parse JSON
                        error_code = error_json.get("error")
                        error_description = error_json.get("error_description")
                        if error_code == "authorization_pending":
                            time.sleep(self._poll_interval)  # Wait before polling again
                        elif error_code == "slow_down":
                            self._poll_interval += (
                                5  # Adjust polling interval if required
                            )
                            time.sleep(self._poll_interval)
                        else:
                            raise Exception(
                                f"⚠️ Authentication failed: [{error_code}] {error_description}"
                            )
                    except json.JSONDecodeError:
                        print(
                            "❌ Failed to parse JSON from exception message.  Please re-run the command."
                        )
                else:
                    _logger.error(
                        f"Unhandled Exception: {e}.  Please re-run the command."
                    )
                    break

            if datetime.datetime.now() > timeout_time:
                print("❌ Failed to authenticate!  Please re-run the command.")
                return False

    def _start_auth_flow(self):
        print("\n🔐 No active session. Please sign in to continue.")
        if not self._get_device_code():
            return False
        return self._poll_for_token()

    def _check_if_expired(self, leeway: datetime.timedelta = datetime.timedelta()):
        """Check the token in self._token_data and check if it is expired

        If [leeway] is set then this function will consider the token expired if it is going to
        expire within [leeway] amount of time.

        Raises:
            RuntimeError: _description_

        Returns:
            bool: True if it is expired, False otherwise
        """

        if self._token_data is None:
            raise RuntimeError(
                "Can't check if token is expired because there is no token!  Please login first."
            )

        access_token = self._token_data["access_token"]
        response_data = self._make_http_request(
            "POST",
            "/device-auth/remaining-time",
            headers={
                "Authorization": f"Bearer {access_token}",
                "breathe-design-version": __version__,
            },
        )
        if response_data.status_code == 401:
            # unauthorised so we need to login again
            return True

        if response_data.status_code != 200:
            raise RuntimeError(
                f"Failed to check token expiration! {response_data.status_code}"
            )
        response_data = response_data.json()

        # check expiry time including any leeway
        expired = response_data["time_left_s"] <= leeway.total_seconds()

        return expired

    def _get_new_token_from_refresh_token(self):
        """Retrives a new token using the refresh token.

        If successful, this updates the self._token_data with the new token data.

        Raises:
            RuntimeError: _description_
            RuntimeError: _description_
        """
        if (self._token_data is None) or ("refresh_token" not in self._token_data):
            print("No refresh token available.  You must log in again")
            self._token_data = None
            return False

        access_token = self._token_data["access_token"]
        refresh_token = self._token_data["refresh_token"]
        response = self._make_http_request(
            "POST",
            "/device-auth/refresh",
            payload={"refresh_token": refresh_token},
            headers={
                "accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
                "breathe-design-version": __version__,
            },
        )
        if response.status_code != 200:
            # failed to refresh
            return False

        self._token_data = response.json()
        self._save_token_to_tmp()
        return True

    def _refresh_or_start(self):
        """Run token refresh using refresh token.
        If that fails, restart the auth flow to require login again

        Raises:
            RuntimeError: _description_
        """
        if not self._get_new_token_from_refresh_token():
            # if refreshing failed, we need to log in again
            if not self._start_auth_flow():
                raise RuntimeError("Failed to get access token")

    def get_token(self):
        """Returns the current access token. If missing, prompts the user to sign in."""
        with self._lock:
            if not self._token_data:
                if not self._start_auth_flow():
                    raise RuntimeError("Failed to get access token")

                #  immediately refresh because if this was just after signup, the token may not have the correct permissions set yet
                self._refresh_or_start()
            else:
                # we have a token, but check the expiry and if it will expire within the next 5 mins try to refresh it with the refresh token.
                # However if we already checked within the last 5 seconds, don't check again.
                # If we already checked within that time, then whatever the outcome was then won't have changed (because we check for expiry within the next 5 mins).
                # (we do this rate check this to prevent the token check endpoint from being called rapidly e.g. if there are multiple threads getting tokens, and
                # triggering a 429 on the endpoint)
                if (
                    datetime.datetime.now() - self._last_time_token_checked
                    > datetime.timedelta(seconds=5)
                ):
                    self._last_time_token_checked = datetime.datetime.now()
                    if self._check_if_expired(leeway=datetime.timedelta(minutes=5)):
                        self._refresh_or_start()
                else:
                    _logger.debug(
                        "Skipping token expiry check because it was checked recently"
                    )

            return self._token_data["access_token"]

    def logout(self):
        """Log out from the Breathe API.
        This consists of logging out of the OAuth system and then deleting the local token storage.
        """
        try:
            response = self._make_http_request(
                "POST",
                "/device-auth/logout",
                payload={"id_token": self._token_data["id_token"]},
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._token_data['access_token']}",
                    "breathe-design-version": __version__,
                },
            )
            if response.status_code != 200:
                msg = f"Error logging out!: {response.status_code}"
                if response.content:
                    msg += f": {response.content}"
                _logger.error(msg)
        except:  # noqa
            # if we fail to log out, no matter, still delete the token requiring us to get a new one
            pass
        with self._lock:
            self._token_data = None
            self._delete_tmp_token_file()


device_auth = _DeviceFlowAuth()
