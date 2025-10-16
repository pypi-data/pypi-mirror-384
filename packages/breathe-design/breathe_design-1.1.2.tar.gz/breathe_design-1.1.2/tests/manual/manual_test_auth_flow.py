"""
This script is a manual test to check that the authorisation works properly.

To test, run the script and just check that it gets to the end and prints out "Everything worked correctly!"
"""

from breathe_design.device_flow_auth import _DeviceFlowAuth

auth = _DeviceFlowAuth()

# try to get the token (which will require us to log in)
auth.get_token()

assert auth._token_data
assert "access_token" in auth._token_data

# check it is not expired
assert not auth._check_if_expired()

# get a new token from refresh
assert auth._get_new_token_from_refresh_token()

assert auth._token_data
assert "access_token" in auth._token_data
assert not auth._check_if_expired()

# log out
auth.logout()

print("Everything worked correctly!")
