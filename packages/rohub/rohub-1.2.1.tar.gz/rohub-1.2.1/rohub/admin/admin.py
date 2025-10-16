from rohub import settings
from rohub import utils
from rohub import rohub

import functools


def validate_authentication_token(func):
    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
        if utils.is_valid(token_type="access"):
            valid_token = True
        else:
            valid_token = utils.refresh_access_token()
        if valid_token:
            return func(*args, **kwargs)
    return func_wrapper


def validate_admin_permissions(func):
    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
        profile_details = rohub.show_my_user_profile_details()
        roles = profile_details.get("roles", "unknown")  # if for some reason we could not find roles, set it to unknown
        if "admin" not in roles:
            print("Account you are currently logged in doesn't have admin permissions!")
            print("Therefore, you are not allowed to execute this action!")
            return
        else:
            return func(*args, **kwargs)
    return func_wrapper


@validate_authentication_token
@validate_admin_permissions
def delete_external_user(user_identifier):
    """
    Function that deletes specific external user.

    .. warning::
        The operation is permitted only if you are logged into account with admin privileges

    :param user_identifier: user's identifier
    :type user_identifier: str
    :returns: response/None
    :rtype: dict/None
    """
    url = settings.API_URL + f"external_users/{user_identifier}/"
    r = utils.delete_request(url=url)
    if r.status_code != 204:
        content = r.json()
        return content
    else:
        print("User successfully deleted!")
        return


@validate_authentication_token
@validate_admin_permissions
def delete_organization(organization_identifier):
    """
    Function that deletes specific organization.

    .. warning::
        The operation is permitted only if you are logged into account with admin privileges

    :param organization_identifier: user's identifier
    :type organization_identifier: str
    :returns: response/None
    :rtype: dict/None
    """
    url = settings.API_URL + f"organizations/{organization_identifier}/"
    r = utils.delete_request(url=url)
    if r.status_code != 204:
        content = r.json()
        return content
    else:
        print("Organization successfully deleted!")
        return


@validate_authentication_token
@validate_admin_permissions
def delete_community(community_identifier):
    """
    Function that deletes a specific community based on its identifier.

    .. warning::
        The operation is permitted only if you are logged into account with admin privileges

    :param community_identifier: community identifier
    :rtype identifier: str
    :returns: response content from the API
    :rtype: dict
    """
    url = settings.API_URL + f"communities/{community_identifier}/"
    r = utils.delete_request(url=url)
    if r.status_code != 204:
        content = r.json()
        return content
    else:
        print("Community successfully deleted!")
        return


@validate_authentication_token
@validate_admin_permissions
def update_community(identifier, name=None, description=None, email=None, community_url=None):
    """
    Function that updates a specific community.

    .. warning::
        The operation is permitted only if you are logged into account with admin privileges

    :param identifier: communities identifier
    :type identifier: str
    :param name: community name, optional
    :type name: str
    :param description: community description, optional
    :type description: str
    :param email: communities email, optional
    :type: email: str
    :param community_url: associated url, optional
    :type: community_url: str
    :returns: response content from the API
    :rtype: dict
    """
    data = {"name": name,
            "description": description,
            "email": email,
            "url": community_url}
    data = {key: value for key, value in data.items() if value is not None}
    url = settings.API_URL + f"communities/{identifier}/"
    r = utils.patch_request(url=url, data=data)
    content = r.json()
    return content


@validate_authentication_token
@validate_admin_permissions
def delete_custom_license(license_id):
    """
    Function that deletes selectec custom license.

    .. warning::
        The operation is permitted only if you are logged into account with admin privileges

    :param license_id: license identifier
    :type: license_id: str
    :returns: None
    :rtype: None
    """
    url = settings.API_URL + f"custom-licenses/{license_id}/"
    r = utils.delete_request(url=url)
    if r.status_code != 204:
        content = r.json()
        return content
    else:
        print("License successfully deleted!")
        return


@validate_authentication_token
@validate_admin_permissions
def update_custom_license(identifier, title, status, license_url, description=None):
    """
    Function that updates a custom license.

    .. seealso::
        :func:`~rohub.list_valid_license_status`

    .. warning::
        The operation is permitted only if you are logged into account with admin privileges

    :param identifier: license's identifier
    :type identifier: str
    :param title: license's title
    :type title: str
    :param status: license's status
    :type status: str
    :param license_url: license's url
    :type license_url: str
    :param description: license's description, optional
    :type description: str
    :returns: response content from the API
    :rtype: dict
    """
    try:
        valid_status = set(rohub.list_valid_license_status())
        verified_status = utils.validate_against_different_formats(input_value=status,
                                                                   valid_value_set=valid_status)
        # checking if set contains at least one element
        if len(verified_status):
            # expected behaviour, only one value is correct
            status = verified_status[0]
        else:
            msg = f"Incorrect license status. Must be one of: {valid_status}"
            raise SystemExit(msg)
    except Exception as e:
        msg = "Unexpected error: couldn't validate license status value."
        print(msg)
        print(e)

    url = settings.API_URL + f"custom-licenses/{identifier}/"
    data = {"identifier": identifier,
            "title": title,
            "status": status,
            "url": license_url,
            "description": description}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.put_request(url=url, data=data, use_token=True)
    content = r.json()
    return content
