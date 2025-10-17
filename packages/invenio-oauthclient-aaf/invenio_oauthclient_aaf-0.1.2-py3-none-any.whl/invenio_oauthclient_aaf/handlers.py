"""AAF OAuth handlers for user account information."""

from flask import current_app


def account_info(remote, resp):
    """Retrieve AAF account information from userinfo endpoint.

    Args:
        remote: The OAuth remote application
        resp: The OAuth response containing access token

    Returns:
        dict: User information formatted for InvenioRDM
    """
    # Get the access token from the response
    access_token = resp.get("access_token")

    if not access_token:
        raise Exception("No access token received from AAF")

    # Call AAF's userinfo endpoint
    try:
        userinfo_url = current_app.config.get("AAF_USERINFO_URL")
        user_info_response = remote.get(userinfo_url)

        user_info = user_info_response.data

    except Exception as e:
        raise e

    # Validate required fields
    if not user_info.get("email"):
        raise Exception("AAF did not provide user email")

    if not user_info.get("sub"):
        raise Exception("AAF did not provide user ID (sub)")

    # Map AAF attributes to InvenioRDM user model
    # Get username, fallback to email prefix if preferred_username not
    # available
    preferred_username = user_info.get("preferred_username")
    if preferred_username:
        username = preferred_username.replace(" ", "_")
    else:
        username = user_info.get("email", "").split("@")[0]

    return {
        "user": {
            "email": user_info.get("email"),
            "profile": {
                "full_name": user_info.get("name", ""),
                "username": username,
            },
        },
        "external_id": user_info.get("sub"),  # AAF's unique user identifier
        "external_method": "aaf",
    }


def account_setup(remote, token, resp):
    """Perform additional setup after user have been logged in.

    :param remote: The remote application.
    :param token: The token value.
    :param resp: The response.
    """
    ...
