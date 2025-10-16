# Standard library imports
import os
import zipfile
import json
import shutil
import functools

# Third party imports
import requests
import pandas as pd
from pandas.errors import ParserError
import numpy as np

# Internal imports
import rohub
from rohub import settings, utils, memo
from rohub.ResearchObject import ResearchObject
from rohub.Resource import Resource
from rohub.Folder import Folder
from rohub._version import __version__


###############################################################################
#              Decorators.                                                    #
###############################################################################

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


###############################################################################
#              Main Methods.                                                  #
###############################################################################

def login(username=None, password=None, client_id=None, client_secret=None):
    """
    | Function that handles access token generation and results in saving token information throughout the session.
    | There are two ways of authenticating:
    | 1) User authentication (username and password required)
    | 2) Client authentication (client_id and client_secret required)

    :param username: username for user authentication, optional
    :type username: str
    :param password: password for user authentication, optional
    :type password: str
    :param client_id: client id for client authentication, optional
    :type client_id: str
    :param client_secret: client secret for client authentication, optional
    :type client_secret: str
    :returns: None
    :rtype: None
    """
    url = settings.KEYCLOAK_URL
    if username and password:
        settings.USERNAME = username
        settings.PASSWORD = password
        settings.GRANT_TYPE = "password"
        data = {'client_id': settings.KEYCLOAK_CLIENT_ID,
                'client_secret': settings.KEYCLOAK_CLIENT_SECRET,
                'username': settings.USERNAME,
                'password': settings.PASSWORD,
                'grant_type': settings.GRANT_TYPE}
    elif client_id and client_secret:
        settings.KEYCLOAK_CLIENT_ID = client_id
        settings.KEYCLOAK_CLIENT_SECRET = client_secret
        settings.GRANT_TYPE = "client_credentials"
        settings.USERNAME = f"service-account-{client_id}"
        data = {'client_id': settings.KEYCLOAK_CLIENT_ID,
                'client_secret': settings.KEYCLOAK_CLIENT_SECRET,
                'username': settings.USERNAME,
                'grant_type': settings.GRANT_TYPE}
    else:
        msg = "Incomplete input. To authenticate the user please provide username and password or" \
              " provide client_id and client_secret to authenticate using client!"
        raise SystemExit(msg)
    try:
        r = requests.post(url, data=data, timeout=settings.TIMEOUT)
        r.raise_for_status()
        r_json = r.json()
        settings.ACCESS_TOKEN = r_json.get('access_token')
        settings.ACCESS_TOKEN_VALID_TO = utils.valid_to(exp_time=r_json.get('expires_in'),
                                                        token_type="access token")
        settings.REFRESH_TOKEN = r_json.get('refresh_token')
        settings.REFRESH_TOKEN_VALID_TO = utils.valid_to(exp_time=r_json.get('refresh_expires_in'),
                                                         token_type="refresh token")
        settings.TOKEN_TYPE = r_json.get('token_type')
        settings.SESSION_STATE = r_json.get('session_state')
        print(f"Logged successfully as {settings.USERNAME}.")
    except requests.exceptions.HTTPError as e:
        print("Http error occurred.")
        print(e.response.text)
        raise e
    except requests.exceptions.ConnectionError:
        try:
            print("Connection error occurred. Trying again...")
            requests.post(url, data=data, timeout=settings.TIMEOUT)
        except requests.exceptions.ConnectionError as e:
            print("Connection error occurred for a second time. Aborting...")
            raise SystemExit(e.response.text)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)
    except requests.exceptions.Timeout as e:
        print("Timeout. Could not connect to the server.")
        raise SystemExit(e.response.text)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)


def whoami():
    """
    Function that returns service username for user that is currently logged in.

    :returns: username
    :rtype: str
    """
    if settings.USERNAME:
        return settings.USERNAME
    else:
        return "Currently not logged in!"


def version():
    """
    Displays the current package version.

    :returns: package version
    :rtype: str
    """
    return f"You are currently using package {__version__}."


def set_retries(number_of_retries):
    """
    Function that sets up maximum number of retries for validating a response status.

    .. note::
        You may want to increase number of retries or sleep time in case your job status
        validations ends up with information that there was not enough time to validate
        the status of the job. This can be dependent on current API traffic.

    :param number_of_retries: maximum number of retries
    :type number_of_retries: int
    :returns: None
    :rtype: None
    """
    if not isinstance(number_of_retries, int):
        print(f"number_of_retries has to be an integer, not {type(number_of_retries)}!")
    else:
        settings.RETRIES = number_of_retries
        print(f"number of retries is now changed to {settings.RETRIES}.")


def set_sleep_time(sleep_time):
    """
    Function that sets up sleep time for between requests for validating a response status.

    .. note::
        You may want to increase number of retries or sleep time in case your job status
        validations ends up with information that there was not enough time to validate
        the status of the job. This can be dependent on current API traffic.

    :param sleep_time: sleep time
    :type sleep_time: int
    :returns: None
    :rtype: None
    """
    if not isinstance(sleep_time, int):
        print(f"sleep_time has to be an integer, not {type(sleep_time)}!")
    else:
        settings.SLEEP_TIME = sleep_time
        print(f"sleep_time is now changed to {settings.SLEEP_TIME}.")


@validate_authentication_token
def show_my_user_profile_details():
    """
    Function that shows profile details for user that is currently logged in.

    :returns: response
    :rtype: dict
    """
    url = settings.API_URL + f"users/whoami/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    return content


@validate_authentication_token
def list_my_ros():
    """
    Function that lists research objects that belongs to the current user.

    :returns: table with listed research objects
    :rtype: Panda's DataFrame
    """
    url = settings.API_URL + f"search/ros/"
    params = {"owner": settings.USERNAME}
    r = utils.get_request_with_params(url=url, params=params)
    content = r.json()
    results = content.get("results")
    while content["next"]:
        r = utils.get_request(url=content["next"])
        content = r.json()
        results.extend(content.get("results"))
    df = pd.DataFrame(results)
    if not df.empty:
        selected_columns = ['identifier', 'shared_link', 'title', 'description', 'created_on',
                            'created_by', 'modified_on', 'type', 'status', 'access_mode', 'owner',
                            'research_areas', 'creation_mode']
        df.drop(df.columns.difference(selected_columns), axis=1, inplace=True)
        column_sequence = ["identifier", "title", "description", "type", "research_areas",
                           "status", "created_on", "created_by", "modified_on", "access_mode",
                           "owner", "creation_mode", "shared_link"]
        df = df.reindex(columns=column_sequence)
    return df


@validate_authentication_token
def is_job_success(job_id):
    """
    Function that checks the status of the job and validate if job succeed or not.

    :param job_id: job's identifier
    :type job_id: str
    :returns: response
    :rtype: dict
    """
    job_url = settings.API_URL + f"jobs/{job_id}/"
    job_r = utils.get_request(url=job_url, use_token=True)
    job_content = job_r.json()
    job_status = job_content['status']
    if job_status == "SUCCESS":
        return job_content
    elif job_status == "FAILURE":
        msg = f"Job failed with the following info: {job_content['output']}"
        raise SystemExit(msg)
    elif job_status == "WARNING":
        msg = f"Job succeeded but there is a following warning associated with it: {job_content['warnings']}"
        print(msg)
        return job_content
    else:
        print("Trying to confirm status of the job. It can take a while...")
        job_success = utils.check_for_status(job_url=job_url)
        if job_success:
            # updating response after success.
            job_r = utils.get_request(url=job_url, use_token=True)
            job_content = job_r.json()
            job_status = job_content['status']
            if job_status == "SUCCESS":
                return job_content
            elif job_status == "WARNING":
                msg = f"Job succeeded but there is a following warning associated with it: " \
                      f"{job_content['warnings']}"
                print(msg)
                return job_content
            else:
                msg = f"Job failed with the following info: {job_content['output']}"
                raise SystemExit(msg)
        else:
            msg = f"""Couldn't validate if uploading ended up with a success given the time limit.
                    You can try increasing retries through set_retries() and sleep time through 
                    set_sleep_time() functions and re-run it. You can also check if the current job
                    eventually succeeded by running is_job_success(job_id="{job_id}")"""
            raise SystemExit(msg)


###############################################################################
#              ROS main methods.                                              #
###############################################################################

@validate_authentication_token
def ros_find(search=None):
    """
    Function that finds a specific research object against provided query.

    :param search: phrase to search against, optional
    :type search: str
    :returns: table containing selected information about the research object/objects
    :rtype: Panda's DataFrame
    """
    url = settings.API_URL + f"search/ros/"
    if search:
        params = {"search": search}
        r = utils.get_request_with_params(url=url, params=params)
    else:
        r = utils.get_request(url=url)
    content = r.json()
    results = content.get("results")
    while content["next"]:
        r = utils.get_request(url=content["next"])
        content = r.json()
        results.extend(content.get("results"))
    df = pd.DataFrame(results)
    if not df.empty:
        selected_columns = ['identifier', 'shared_link', 'title', 'description', 'created_on',
                            'created_by', 'modified_on', 'type', 'status', 'access_mode', 'owner',
                            'research_areas', 'creation_mode', 'geoshape', 'completeness', 'completeness_calculated_on',
                            'rating', 'number_of_resources', 'number_of_folders', 'number_of_annotations',
                            'number_of_all_aggregates', 'number_of_ratings', 'number_of_likes', 'number_of_dislikes',
                            'number_of_downloads', 'number_of_views', 'number_of_snapshots', 'number_of_forks',
                            'number_of_archives', 'number_of_events', 'number_of_references', 'main_entity',
                            'communities', 'score', 'keywords', 'domains', 'places', 'organizations', 'persons',
                            'concepts']
        df.drop(df.columns.difference(selected_columns), axis=1, inplace=True)
        column_sequence = ["identifier", "title", "description", "type", "research_areas",
                           "status", "created_on", "created_by", "modified_on", "access_mode",
                           "owner", "creation_mode", "completeness", "completeness_calculated_on",
                           "rating", "geoshape", "number_of_resources", "number_of_folders", "number_of_annotations",
                           "number_of_all_aggregates", "number_of_ratings", "number_of_likes", "number_of_dislikes",
                           "number_of_downloads", "number_of_views", "number_of_snapshots", "number_of_forks",
                           "number_of_archives", "number_of_events", "number_of_references", "main_entity",
                           "communities", "score", "keywords", "domains", "places", "organizations", "persons",
                           "concepts", "shared_link"]
        df = df.reindex(columns=column_sequence)
    return df


@validate_authentication_token
def ros_find_using_geoshape(bounding_box):
    """
    Function that finds a research object/research objects related to a specific bounding box.

    :param bounding_box: list containing four coordinates that do establish a bounding box.
    :type bounding_box: list
    :returns: table containing selected information about the research object/objects
    :rtype: Panda's DataFrame
    """
    url = settings.API_URL + f"search/ros/"
    converted_bounding_box = f"{str(bounding_box[0])},{str(bounding_box[1])}__{str(bounding_box[2])}," \
                             f"{str(bounding_box[3])}__relation,within__type,envelope"
    params = {"geoshape__geo_shape": converted_bounding_box}
    r = utils.get_request_with_params(url=url, params=params)
    content = r.json()
    results = content.get("results")
    while content["next"]:
        r = utils.get_request(url=content["next"])
        content = r.json()
        results.extend(content.get("results"))
    df = pd.DataFrame(results)
    if not df.empty:
        selected_columns = ['identifier', 'shared_link', 'title', 'description', 'created_on',
                            'created_by', 'modified_on', 'type', 'status', 'access_mode', 'owner',
                            'research_areas', 'creation_mode', 'geoshape', 'completeness', 'completeness_calculated_on',
                            'rating', 'number_of_resources', 'number_of_folders', 'number_of_annotations',
                            'number_of_all_aggregates', 'number_of_ratings', 'number_of_likes', 'number_of_dislikes',
                            'number_of_downloads', 'number_of_views', 'number_of_snapshots', 'number_of_forks',
                            'number_of_archives', 'number_of_events', 'number_of_references', 'main_entity',
                            'communities', 'score', 'keywords', 'domains', 'places', 'organizations', 'persons',
                            'concepts']
        df.drop(df.columns.difference(selected_columns), axis=1, inplace=True)
        column_sequence = ["identifier", "title", "description", "type", "research_areas",
                           "status", "created_on", "created_by", "modified_on", "access_mode",
                           "owner", "creation_mode", "completeness", "completeness_calculated_on",
                           "rating", "geoshape", "number_of_resources", "number_of_folders", "number_of_annotations",
                           "number_of_all_aggregates", "number_of_ratings", "number_of_likes", "number_of_dislikes",
                           "number_of_downloads", "number_of_views", "number_of_snapshots", "number_of_forks",
                           "number_of_archives", "number_of_events", "number_of_references", "main_entity",
                           "communities", "score", "keywords", "domains", "places", "organizations", "persons",
                           "concepts", "shared_link"]
        df = df.reindex(columns=column_sequence)
    return df


@validate_authentication_token
def ros_search_using_id(identifier):
    """
    Function that finds research object based on its identifier.

    :param identifier: research object identifier
    :type identifier: str
    :returns: response containing details for the research object
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    return content


@validate_authentication_token
def ros_create(title, research_areas, description=None, access_mode=None,
               ros_type=None, use_template=False, owner=None, editors=None,
               readers=None, creation_mode=None):
    """
    Function that creates new Research Object in the API and instantiates a Python object that can be reused.

    .. seealso::
        | :func:`~list_valid_research_areas`
        | :func:`~list_valid_access_modes`
        | :func:`~list_valid_ros_types`
        | :func:`~list_valid_templates`
        | :func:`~list_valid_creation_modes`

    .. note::
        The newly created research object will return a Python object that has its own set of methods
        and attributes. You may want to assign it to a variable to make it easy to work with.
        For example: ``my_ros = ros_create(**your set of params)``

    :param title: title of your research object
    :type title: str
    :param research_areas: research areas associated with your research object
    :type research_areas: list
    :param description: description of your research object, optional
    :type description: str
    :param access_mode: research object's access mode, optional
    :type access_mode: str
    :param ros_type: research object's type, optional
    :type ros_type: str
    :param use_template: if True appropriate template for ro type will be used, optional
    :type use_template: bool
    :param owner: research object's owner, optional
    :type owner: str
    :param editors: research object's editors, optional
    :type editors: list
    :param readers: research object's readers, optional
    :type readers: list
    :param creation_mode: research object's creation mode, optional
    :type creation_mode: str
    :returns: newly created research object
    :rtype: ResearchObject
    """
    return ResearchObject.ResearchObject(title=title, research_areas=research_areas,
                                         description=description, access_mode=access_mode,
                                         ros_type=ros_type, use_template=use_template, owner=owner,
                                         editors=editors, readers=readers, creation_mode=creation_mode,
                                         post_request=True)


@validate_authentication_token
def ros_load(identifier):
    """
    Function that loads an existing research object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: loaded research object
    :rtype: ResearchObject
    """
    return ResearchObject.ResearchObject(identifier=identifier, post_request=False)


@validate_authentication_token
def ros_content(identifier):
    """
    Function that retrieves research object's content based on its identifier.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: response containing details for research object's content
    :rtype: dict
    """
    if utils.is_valid(token_type="access"):
        url = settings.API_URL + f"ros/{identifier}/content/full"
        r = utils.get_request(url=url, use_token=True)
        content = r.json()
        return content
    else:
        msg = "Your current access token is either missing or expired, please log into" \
              " rohub again"
        raise SystemExit(msg)


@validate_authentication_token
def ros_full_metadata(identifier):
    """
    Function that retrieves research object's full metadata based on identifier.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: response containing details for research object's content
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/full/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    return content


@validate_authentication_token
def ros_fork(identifier, title=None, description=None):
    """
    Function that creates research object's fork.

    :param identifier: research object's identifier
    :type identifier: str
    :param title: fork title, optional
    :type title: str
    :param description: fork description, optional
    :type description: str
    :returns: fork identifier
    :rtype: str
    """
    url = settings.API_URL + f"ros/{identifier}/evolution/"
    data = {"status": "FORK",
            "title": title,
            "description": description}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    job_id = content["identifier"]
    if job_id:
        fork_response = is_job_success(job_id=job_id)
        forked_results = fork_response.get("results")
        fork_warnings = fork_response.get("warnings")
        if fork_warnings:
            print(f"WARNING: {fork_warnings}")
        if forked_results:
            forked_ros_id = forked_results.split("/")[-2]
            return forked_ros_id
    else:
        msg = "Incorrect job response, couldn't validate if file was uploaded or not."
        raise SystemExit(msg)


@validate_authentication_token
def ros_snapshot(identifier, title=None, description=None, create_doi=None,
                 external_doi=None, publication_services=None):
    """
    Function that creates research object's snapshot.

    .. seealso::
        :func:`~rohub.list_valid_publication_services`

    .. note::
        if one chooses to use doi it can be provided in two ways:
        1) through setting create_doi to True, then doi will be generated for you
        2) through passing your doi using external_doi parameter
        create_doi = True and external_doi are mutually exclusive, therefore
        they can't be used simultaneously!

    .. note::
        if on chooses to use publications services the result will be loaded as an RO-crate!

    .. warning::
        user needs to make sure that he has service credentials associated with his profile
        for the publication services that he would like to use!
        If that is not the case, warning will be shown and the ros will not be published as intended!

    :param identifier: research object's identifier
    :type identifier: str
    :param title: snapshot title, optional
    :type title: str
    :param description: snapshot description, optional
    :type description: str
    :param create_doi: doi is created if True, False otherwise, optional, False is the default
    :type create_doi: bool
    :param external_doi: existing doi value that will be associated with the snapshot, optional
    :type external_doi: str
    :param publication_services: services where the snapshot should be published into
    :type publication_services: list
    :returns: snapshot identifier
    :rtype: str
    """
    if create_doi:
        if not isinstance(create_doi, bool):
            msg = f"create_doi parameter has to be a boolean type, not a {type(create_doi)}"
            raise SystemExit(msg)
        if external_doi:
            msg = "Illegal usage: create_doi=True and external_doi are mutually exclusive!"
            raise SystemExit(msg)
    if publication_services:
        validated = []
        try:
            available_services = set(list_valid_publication_services())
            for candidate in publication_services:
                validated.extend(utils.validate_against_different_formats(input_value=candidate,
                                                                          valid_value_set=available_services))
            if validated:
                publication_services = validated
            else:
                publication_services = None
        except KeyError as e:
            print(f"Couldn't validate publication_services value! Omitting this parameter.")
            print(e)
            publication_services = None
    url = settings.API_URL + f"ros/{identifier}/evolution/"
    data = {"status": "SNAPSHOT",
            "title": title,
            "description": description,
            "create_doi": create_doi,
            "external_doi": external_doi,
            "publication_services": publication_services}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    job_id = content["identifier"]
    if job_id:
        snapshot_response = is_job_success(job_id=job_id)
        snapshot_results = snapshot_response.get("results")
        snapshot_warnings = snapshot_response.get("warnings")
        if snapshot_warnings:
            print(f"WARNING: {snapshot_warnings}")
        if snapshot_results:
            snapshot_ros_id = snapshot_results.split("/")[-2]
            return snapshot_ros_id
    else:
        msg = "Incorrect job response, couldn't validate if file was uploaded or not."
        raise SystemExit(msg)


@validate_authentication_token
def ros_archive(identifier, title=None, description=None, create_doi=None,
                external_doi=None, publication_services=None):
    """
    Function that creates research object's archive.

    .. seealso::
        :func:`~list_valid_publication_services`

    .. note::
        if one chooses to use doi it can be provided in two ways:
        1) through setting create_doi to True, then doi will be generated for you
        2) through passing your doi using external_doi parameter
        create_doi = True and external_doi are mutually exclusive, therefore
        they can't be used simultaneously!

    .. note::
        if on chooses to use publications services the result will be loaded as an RO-crate!

    .. warning::
        user needs to make sure that he has service credentials associated with his profile
        for the publication services that he would like to use!
        If that is not the case, warning will be shown and the ros will not be published as intended!

    :param identifier: research object's identifier
    :type identifier: str
    :param title: archive title, optional
    :type title: str
    :param description: archive description, optional
    :type description: str
    :param create_doi: doi is created if True, False otherwise, optional, False is the default
    :type create_doi: bool
    :param external_doi: existing doi value that will be associated with the snapshot, optional
    :type external_doi: str
    :param publication_services: services where the archive should be published into
    :type publication_services: list
    :returns: archive identifier
    :rtype: str
    """
    if create_doi:
        if not isinstance(create_doi, bool):
            msg = f"create_doi parameter has to be a boolean type, not a {type(create_doi)}"
            raise SystemExit(msg)
        if external_doi:
            msg = "Illegal usage: create_doi=True and external_doi are mutually exclusive!"
            raise SystemExit(msg)
    if publication_services:
        validated = []
        try:
            available_services = set(list_valid_publication_services())
            for candidate in publication_services:
                validated.extend(utils.validate_against_different_formats(input_value=candidate,
                                                                          valid_value_set=available_services))
            if validated:
                publication_services = validated
            else:
                publication_services = None
        except KeyError as e:
            print(f"Couldn't validate publication_services value! Omitting this parameter.")
            print(e)
            publication_services = None
    url = settings.API_URL + f"ros/{identifier}/evolution/"
    data = {"status": "ARCHIVE",
            "title": title,
            "description": description,
            "create_doi": create_doi,
            "external_doi": external_doi,
            "publication_services": publication_services}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    job_id = content["identifier"]
    if job_id:
        archive_response = is_job_success(job_id=job_id)
        archive_results = archive_response.get("results")
        archive_warnings = archive_response.get("warnings")
        if archive_warnings:
            print(f"WARNING: {archive_warnings}")
        if archive_results:
            archive_ros_id = archive_results.split("/")[-2]
            return archive_ros_id
    else:
        msg = "Incorrect job response, couldn't validate if file was uploaded or not."
        raise SystemExit(msg)


def ros_list_publications(identifier):
    """
    Function that lists publication details related to specific research object.

    :param identifier: research object's identifier.
    :type identifier: str
    :return: set of selected information regarding each publication
    :rtype: list
    """
    url = settings.API_URL + f"ros/{identifier}/publications/"
    r = utils.get_request(url=url, use_token=False)
    content = r.json()
    results = content.get("results")
    while content["next"]:
        r = utils.get_request(url=content["next"])
        content = r.json()
        results.extend(content.get("results"))
    publications = []
    for result in results:
        publications.append({"doi": result.get("doi"),
                             "storage": result.get("storage"),
                             "storage_record_id": result.get("storage_record_identifier")})
    return publications


def ros_triple_details(identifier):
    """
    Function that shows details for triple based on it's identifier.

    :param identifier: triple's identifier
    :type identifier: str
    :returns: response containing triple details
    :rtype: dict
    """
    url = settings.API_URL + f"triples/{identifier}"
    r = utils.get_request(url=url, use_token=False)
    content = r.json()
    return content


@validate_authentication_token
def ros_list_annotations(identifier):
    """
    Function that lists all annotations associated with specific research object.

    :param identifier: research object's identifier.
    :type identifier: str
    :return: set of selected information regarding each annotation
    :rtype: list
    """
    url = settings.API_URL + f"ros/{identifier}/annotations/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    results = content.get("results")
    while content["next"]:
        r = utils.get_request(url=content["next"])
        content = r.json()
        results.extend(content.get("results"))
    annotations = []
    for result in results:
        annotations.append({"identifier": result.get("identifier"),
                            "name": result.get("name"),
                            "filename": result.get("filename"),
                            "created": result.get("created"),
                            "creator": result.get("creator")})
    return annotations


@validate_authentication_token
def ros_list_triples(identifier):
    """
    Function that lists all triples related to a specific annotation.

    :param identifier: annotation's identifier
    :type identifier: str
    :return: set of selected information regarding each triple
    :rtype: list
    """
    url = settings.API_URL + f"annotations/{identifier}/body/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    results = content.get("results")
    while content["next"]:
        r = utils.get_request(url=content["next"])
        content = r.json()
        results.extend(content.get("results"))
    triples = []
    for result in results:
        triples.append({"identifier": result.get("identifier"),
                        "subject": result.get("subject"),
                        "predicate": result.get("predicate"),
                        "object": result.get("object"),
                        "created_by": result.get("created_by"),
                        "created_on": result.get("created_on")})
    return triples


@validate_authentication_token
def ros_list_authors(identifier):
    """
    Function that lists authors associated with certain research object.

    :param identifier: research object's identifier.
    :type identifier: str
    :returns: response containing authors details
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/authors/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    return content


@validate_authentication_token
def ros_list_contributors(identifier):
    """
    Function that lists contributors associated with certain research object.

    :param identifier: research object's identifier.
    :type identifier: str
    :returns: response containing contributors details
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/contributors/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    return content


@validate_authentication_token
def ros_list_publishers(identifier):
    """
    Function that lists publishers associated with certain research object.

    :param identifier: research object's identifier.
    :type identifier: str
    :returns: response containing contributors details
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/publisher/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    return content


@validate_authentication_token
def ros_list_copyright_holders(identifier):
    """
    Function that lists copyright holders associated with certain research object.

    :param identifier: research object's identifier.
    :type identifier: str
    :returns: response containing copyright details
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/copyright/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    return content


@validate_authentication_token
def ros_list_fundings(identifier):
    """
    Function that lists fundings associated with certain research object.

    :param identifier: research object's identifier.
    :type identifier: str
    :returns: table containing selected information about funding
    :rtype: Panda's DataFrame
    """
    url = settings.API_URL + f"ros/{identifier}/fundings/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    df = pd.DataFrame(content.get("results"))
    if not df.empty:
        try:
            df_a = pd.json_normalize(df["grant"])   # exploding grant part to df
            df_a.rename(columns={"identifier": "grant_id", "name": "grant_name", "title": "grant_title"},
                        inplace=True)
            df_b = pd.json_normalize(df["funder"])   # exploding funder part to df
            df_b.rename(columns={"type": "funder_type", "doi": "funder_doi", "name": "funder_name"}, inplace=True)
            df.drop(["grant", "funder"], axis=1, inplace=True)   # those are no longer needed
            df.rename(columns={"identifier": "funding_id", "type": "funding_type"}, inplace=True)
            df = df.join([df_a, df_b])
        # in case anything goes wrong lets return original dataframe with results
        except Exception:
            pass
    return df


@validate_authentication_token
def ros_list_license(identifier):
    """
    Function that lists license associated with certain research object.

    :param identifier: research object's identifier.
    :type identifier: str
    :returns: response containing license details
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/license/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    return content


@validate_authentication_token
def ros_list_resources(identifier):
    """
    Function that lists resources associated with specific research object.

    :param identifier: research object's identifier.
    :type identifier: str
    :returns: table containing selected information about all associated resources
    :rtype: Panda's DataFrame
    """
    url = settings.API_URL + f"ros/{identifier}/resources/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    results = content.get("results")
    while content["next"]:
        r = utils.get_request(url=content["next"])
        content = r.json()
        results.extend(content.get("results"))
    df = pd.DataFrame(results)
    if not df.empty:
        selected_columns = ["identifier", "type", "title", "description", "url", "name",
                            "path", "size", "creator", "created_on", "modified_on", "download_url"]
        df.drop(df.columns.difference(selected_columns), axis=1, inplace=True)
        df["source"] = np.where(df["url"].isna(), "internal", "external")
        column_sequence = ["identifier", "type", "source", "title", "description", "url", "name",
                           "path", "size", "creator", "created_on", "modified_on", "download_url"]
        df = df.reindex(columns=column_sequence)
    return df


@validate_authentication_token
def ros_list_folders(identifier):
    """
    Function that lists folders associated with specific research object.

    :param identifier: research object's identifier.
    :type identifier: str
    :returns: table containing selected information about all associated folders
    :rtype: Panda's DataFrame
    """
    url = settings.API_URL + f"ros/{identifier}/folders/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    results = content.get("results")
    while content["next"]:
        r = utils.get_request(url=content["next"])
        content = r.json()
        results.extend(content.get("results"))
    df = pd.DataFrame(results)
    if not df.empty:
        selected_columns = ["identifier", "name", "description", "path", "creator",
                            "created_on", "modified_on"]
        df.drop(df.columns.difference(selected_columns), axis=1, inplace=True)
    return df


@validate_authentication_token
def ros_export_to_rocrate(identifier, filename=None, path=None, use_format=settings.EXPORT_TO_ROCRATE_DEFAULT_FORMAT):
    """
    Function for downloading research object's metadata as RO-crate.

    :param identifier: research object's identifier
    :type identifier: str
    :param filename: plain filename without extension, optional - if not provided username will be used instead
    :type filename: str
    :param path: folder path to where file should be downloaded, optional - default is current working directory
    :type path: str
    :param use_format: format choice for acquired data - either jsonld or zip
    :type use_format: str
    :returns: None
    :rtype: None
    """
    if not filename:
        filename = settings.USERNAME
    if path:
        os.makedirs(path, exist_ok=True)
        full_path = os.path.join(path, filename)
    else:
        full_path = os.path.join(filename)
    url = settings.API_URL + f"ros/{identifier}/crate/download/"
    if use_format == "jsonld" or use_format == "json-ld":
        r = utils.get_file_request(url=url, use_token=True)
        with open(f'{full_path}.jsonld', 'wb') as out_file:
            shutil.copyfileobj(r.raw, out_file)
        del r
        if path:
            print(f"File was successfully downloaded into {path}.")
        else:
            print(f"File was successfully downloaded.")
    elif use_format == "zip":
        r = utils.get_file_request(url=url, use_token=True, application_type="application/zip")
        with open(f'{full_path}.zip', 'wb') as out_file:
            out_file.write(r.content)
        del r
        if path:
            print(f"File was successfully downloaded into {path}.")
        else:
            print(f"File was successfully downloaded.")
    else:
        print(f"Incorrect use_format. Has to be one of: json-ld, zip. Instead {use_format} was passed.")


@validate_authentication_token
def ros_read_completeness(identifier, checklist=None, target=None, verbose=False):
    """
    Function for displaying completeness score and related details for a specific research object.

    :param identifier: research object's identifier
    :type identifier: str
    :param checklist: url to the checklist, optional
    :type checklist: str
    :param target: checklist's target, optional
    :type target: str
    :param verbose: if True full details will be displayed, otherwise only score with basic metadata, optional.
    :type verbose: bool
    :returns: completeness information
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/completeness/"
    data = {"checklist": checklist,
            "target": target}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.get_request_with_params(url=url, params=data, use_token=True)
    content = r.json()
    if verbose:
        return content
    else:
        selected_info = {
            "completeness": content.get("completeness"),
            "completeness_calculated_on": content.get("completeness_calculated_on"),
            "shared_link": content.get("shared_link")
        }
        return selected_info


@validate_authentication_token
def ros_assess_completeness(identifier, checklist=None, target=None, verbose=False):
    """
    Function that makes assessment of completeness score and show related details for a specific research object.

    :param identifier: research object's identifier
    :type identifier: str
    :param checklist: url to the checklist, optional
    :type checklist: str
    :param target: checklist's target, optional
    :type target: str
    :param verbose: if True full details will be displayed, otherwise only score with basic metadata, optional.
    :type verbose: bool
    :returns: completeness information
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/completeness/"
    data = {"checklist": checklist,
            "target": target}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    if verbose:
        return content
    else:
        selected_info = {
            "completeness": content.get("completeness"),
            "completeness_calculated_on": content.get("completeness_calculated_on"),
            "shared_link": content.get("shared_link")
        }
        return selected_info


@validate_authentication_token
def ros_enrich(identifier):
    """
    Functions for applying enrichment to the specific research object.

    .. warning::
        The enrichment process can take a while.
        We recommend waiting a few minutes and then checking a job status manually
        by running a prompted command.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: API response
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/enrich/"
    r = utils.post_request_no_data(url=url)
    content = r.json()
    job_id = content['identifier']
    if job_id:
        return is_job_success(job_id=job_id)
        # msg = "The enrichment process may take several minutes. " \
        #       "Research Object's metadata will be automatically updated after the process was finished."
        # print(msg)
        # return
    else:
        msg = "Incorrect job response, couldn't validate if file was uploaded or not."
        raise SystemExit(msg)


@validate_authentication_token
def ros_read_enrichment(identifier):
    """
    Functions for reading enrichment details related to the specific research object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: API response
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/enrich/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    return content


def ros_list_keywords(identifier):
    """
    Function that shows list of keywords for specific Research Object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: response containing keywords details
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/keywords/"
    r = utils.get_request(url=url, use_token=False)
    content = r.json()
    return content


def ros_list_communities(identifier):
    """
    Function that shows list of communities for specific Research Object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: list containing keywords details
    :rtype: list
    """
    url = settings.API_URL + f"ros/{identifier}/communities/"
    r = utils.get_request(url=url, use_token=False)
    content = r.json()
    return content


def ros_list_main_entity(identifier):
    """
    Function that shows what is the main entity of a specific Research Object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: response containing main entity details
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/main_entity/"
    r = utils.get_request(url=url, use_token=False)
    content = r.json()
    return content


def ros_list_sketch(identifier):
    """
    Function that list details about sketch associated with specific Research Object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: response containing main entity details
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/sketch/"
    r = utils.get_request(url=url, use_token=False)
    content = r.json()
    return content


def ros_read_fairness(identifier, report_type=settings.FAIRNESS_DEFAULT_REPORT_TYPE):
    """
    Function that list details about fairness assessment associated with specific Research Object.

    .. note::
        available report detail levels are:
        * CONCISE (overall score, description, calculated_on)
        * STANDARD (contents of CONCISE + list_of_components, number_of_components) + components dict with selected info
        * DETAILED (contents of STANDARD) + components dict with all details for each component

    :param identifier: research object's identifier
    :type identifier: str
    :param report_type: report detail level, default is STANDARD.
    :returns: tuple consisting of DataFrame with general info, and dictionary with details regarding components
    :rtype: tuple (STANDARD, DETAILED), DataFrame (CONCISE)
    """
    if report_type not in settings.FAIRNESS_REPORT_TYPES:
        msg = f"Report type not recognized! It has to be one of the following: {settings.FAIRNESS_REPORT_TYPES}"
        raise SystemExit(msg)
    url = settings.API_URL + f"ros/{identifier}/assess_fairness/"
    r = utils.get_request(url=url, use_token=False)
    content = r.json()
    fairness_report = content.get("fairness_check_report")
    fairness_report_time = content.get("fairness_calculated_on")
    # checking if there is a fairness score, otherwise prompting user to assess it first
    if any(element is None for element in [fairness_report, fairness_report_time]):
        msg = "There is no fairness score associated with this RO, please run ros_assess_fairness() " \
              "first to generate it!"
        raise SystemExit(msg)
    if report_type == "CONCISE":
        df_score = pd.DataFrame.from_dict(fairness_report.get("overall_score"), orient="index", columns=["values"])
        df_time = pd.DataFrame.from_dict({"calculated_on": fairness_report_time}, orient="index", columns=["values"])
        df = pd.concat([df_score.loc[:], df_time])
        return df
    elif report_type == "STANDARD" or report_type == "DETAILED":
        df_score = pd.DataFrame.from_dict(fairness_report.get("overall_score"), orient="index", columns=["values"])
        df_time = pd.DataFrame.from_dict({"calculated_on": fairness_report_time}, orient="index", columns=["values"])
        df = pd.concat([df_score.loc[:], df_time])
        comps = fairness_report.get("components")
        comps_names = [comp.get("name") for comp in comps]
        df.loc['components', 'values'] = comps_names
        df.loc['total_number_of_components', 'values'] = len(comps_names)
        components = utils.generate_components_dict(comps=comps, level=report_type)
        return df, components


@validate_authentication_token
def ros_assess_fairness(identifier):
    """
    Function that requests fairness assessment for a specific Research Object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: response containing main entity details
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/assess_fairness/"
    r = utils.post_request_no_data(url=url)
    content = r.json()
    job_id = content['identifier']
    if job_id:
        return is_job_success(job_id=job_id)
    else:
        msg = "Incorrect job response, couldn't validate if file was uploaded or not."
        raise SystemExit(msg)


@validate_authentication_token
def ros_read_stability(identifier):
    """
    Function that shows stability details related to a specific Research Object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: response containing main entity details
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/stability/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    return content


@validate_authentication_token
def ros_assess_stability(identifier):
    """
    Function that requests stability assessment for a specific Research Object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: response containing main entity details
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/stability/"
    r = utils.post_request_no_data(url=url)
    content = r.json()
    job_id = content['identifier']
    if job_id:
        return is_job_success(job_id=job_id)
    else:
        msg = "Incorrect job response, couldn't validate if file was uploaded or not."
        raise SystemExit(msg)


@validate_authentication_token
def ros_read_extended_analytics(identifier):
    """
    Function that shows extended analytics related to a specific Research Object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: response containing main entity details
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/extended_analytics/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    return content


@validate_authentication_token
def ros_assess_extended_analytics(identifier):
    """
    Function that requests stability assessment for a specific Research Object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: response containing main entity details
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/extended_analytics/"
    r = utils.post_request_no_data(url=url)
    content = r.json()
    job_id = content['identifier']
    if job_id:
        return is_job_success(job_id=job_id)
    else:
        msg = "Incorrect job response, couldn't validate if file was uploaded or not."
        raise SystemExit(msg)


@validate_authentication_token
def ros_show_activities(identifier, verbose=False):
    """
    Function that shows activities that were performed on a specific Research Object.

    :param identifier: research object's identifier
    :type identifier: str
    :param verbose: if True full details will be displayed, otherwise only most important information
    :type: verbose: bool
    :returns: table containing selected information about activities
    :rtype: Panda's DataFrame
    """
    url = settings.API_URL + f"ros/{identifier}/activities/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    if not verbose:
        content = utils.limit_depth(input_list=content, key_to_limit_on=settings.ACTIVITIES_KEY_WITH_CHANGES)
        df = pd.DataFrame(content)
        if not df.empty:
            selected_columns = ['history_type', 'history_object_model', 'history_date', 'username', 'changes',
                                'history_change_reason']
            df.drop(df.columns.difference(selected_columns), axis=1, inplace=True)
            column_sequence = ['history_type', 'history_object_model', 'history_date', 'username', 'changes',
                               'history_change_reason']
            df = df.reindex(columns=column_sequence)
    else:
        df = pd.DataFrame(content)
    return df


@validate_authentication_token
def ros_recommend(identifier):
    """
    Function that recommends a similar research object to the one that was provided.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: response containing main entity details
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/recommend/"
    r = utils.post_request_no_data(url=url)
    content = r.json()
    job_id = content['identifier']
    if job_id:
        return is_job_success(job_id=job_id)
    else:
        msg = "Incorrect job response, couldn't validate if file was uploaded or not."
        raise SystemExit(msg)


@validate_authentication_token
def ros_show_rating(identifier):
    """
    Function that shows average rating for particular RO.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: response containing main entity details
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/rating/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    return content


@validate_authentication_token
def ros_create_permission_link(identifier, valid_to=None):
    """
    Function that generates a permission link to a specific PRIVATE Research Object, so that it can be viewed by
    permission link bearer.

    .. warning::
        Research object's access_mode has to be PRIVATE in order for this function to work!

    .. note::
        if passed, valid_to parameter will try to converted provided string into ISO-like timestamp. In case it fails,
        please try to provide it in a way that helps with recognition i.e. "2025-05-30 19:34" or "2025/12/01".


    :param identifier: research object's identifier
    :type identifier: str
    :param valid_to: string representation for a timestamp that indicates expiration time for the link, optional
    :type valid_to: str
    :returns: shared object identifier
    :rtype: str
    """
    # check if RO is private
    ro_access_mode = rohub.ros_search_using_id(identifier=identifier).get("access_mode")
    if not ro_access_mode == "PRIVATE":
        msg = f"This RO is currently in {ro_access_mode} mode. " \
              f"To perform this action Research Object has to be in PRIVATE access mode, otherwise it makes no sense."
        raise SystemExit(msg)
    if valid_to:
        try:
            valid_to = pd.to_datetime(valid_to)
        except (TypeError, ValueError, ParserError) as e:
            msg = "valid_to was not recognized and couldn't be transformed into timestamp, please try again!"
            raise SystemExit(msg)
    url = settings.API_URL + f"ros/{identifier}/permission_links/"
    data = {"valid_to": valid_to}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    permission_object_id = content.get("identifier")
    return permission_object_id


def ros_show_details_using_permission_id(identifier, permission_id):
    """
    Function that finds research object based on its identifier.

    .. seealso::
        :func:`~ros_create_permission_link`

    :param identifier: research object identifier
    :type identifier: str
    :param permission_id: special permission_identifier that was created to view specific RO
    :type permission_id: str
    :returns: response containing details for the research object
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/"
    headers = {"permission": permission_id}
    r = requests.get(url=url, headers=headers)
    content = r.json()
    return content

###############################################################################
#              ROS add methods.                                               #
###############################################################################


@validate_authentication_token
def ros_add_geolocation(identifier, body_specification_json):
    """
    Function that adds geolocation to a specific research object.

    :param identifier: research object's id
    :type identifier: str
    :param body_specification_json: path to the JSON file or Python serializable object (dict, list)
    :type body_specification_json: str/dict/list
    :returns: response content from the API
    :rtype: dict
    """
    if isinstance(body_specification_json, str):
        if os.path.isfile(body_specification_json):
            file = open(body_specification_json)
            body_specification_json = file.read()
    elif isinstance(body_specification_json, (dict, list)):
        body_specification_json = json.dumps(body_specification_json)
    else:
        print(f"Unexpected type of body_specification_json parameter. {type(body_specification_json)} was passed and"
              f" string (path to file) or dictionary was expected!. Leaving body_specification_json value empty.")
        body_specification_json = None
    url = settings.API_URL + f"ros/{identifier}/geolocation/"
    data = {"ro": identifier,
            "body_specification_json": body_specification_json}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content


@validate_authentication_token
def ros_add_folders(identifier, name, description=None, parent_folder=None):
    """
    Function that adds folders to the specific research object.

    :param identifier: research's object identifier
    :type identifier: str
    :param name: folder's name
    :type name: str
    :param description: folder's description, optional
    :type description: str
    :param parent_folder: parent folder path, optional
    :type parent_folder: str
    :returns: response content from the API
    :rtype: dict
    """
    if parent_folder:
        parent_folder = utils.map_path_to_folder_id(folder_path=parent_folder, ro_identifier=identifier)
    return Folder.Folder(ro_id=identifier, name=name, parent_folder=parent_folder, description=description)


@validate_authentication_token
def ros_add_annotations(identifier, resources=None, body_specification_json=None, body_specification_file=None):
    """
    Function that adds annotations to the specific research object.

    .. note::
        body_specification_json and body_specification_file are mutually exclusive!

    :param identifier: research object's identifier
    :type identifier: str
    :param resources: resources identifier to which annotations will be applied, optional
    :type resources: list
    :param body_specification_json: path to the JSON file or Python serializable object (dict, list), optional
    :type body_specification_json: str/dict/list
    :param body_specification_file: path to the local file containing body specification (JSON, JSON-LD, TTL), optional
    :type body_specification_file: str
    :returns: response content from the API
    :rtype: dict
    """
    if body_specification_json:
        if body_specification_file:
            msg = "Illegal usage: body_specification_json and body_specification_file are mutually exclusive!"
            raise SystemExit(msg)
        if isinstance(body_specification_json, (dict, list)):
            body_specification_json = json.dumps(body_specification_json)
        else:
            print(f"Unexpected type of body_specification_json parameter. {type(body_specification_json)} was passed and"
                  f" dictionary or list was expected!. Leaving body_specification_json value empty.")
    elif body_specification_file:
        if os.path.isfile(body_specification_file):
            multipart_data = {"body_specification_file": open(body_specification_file, 'rb')}
        else:
            print(f"body_specification_file doesn't point to an existing file! Proceeding without.")
    url = settings.API_URL + f"ros/{identifier}/annotations/"
    data = {"ro": identifier,
            "resources": resources,
            "body_specification_json": body_specification_json}
    data = {key: value for key, value in data.items() if value is not None}
    if body_specification_file:
        r = utils.post_request_with_multipart_data_and_regular_data(url=url, data=data, multipart_data=multipart_data)
    else:
        r = utils.post_request(url=url, data=data)
    content = r.json()
    return content


def ros_add_internal_resource(identifier, res_type, file_path, title=None, folder=None, description=None):
    """
    Function that adds internal resource to the specific research object.

    .. seealso::
        :func:`~list_valid_resource_types`

    .. note::
        The newly created resource object will return a Python object that has its own set of methods
        and attributes. You may want to assign it to a variable to make it easy to work with.
        For example: ``my_res = ros_add_internal_resource(**your set of params)``

    :param identifier: research object's identifier
    :type identifier: str
    :param res_type: type of resource
    :type res_type: str
    :param file_path: resource's file path
    :type file_path: str
    :param title: resource's title, optional
    :type title: str
    :param folder: folder's path, optional
    :type folder: str
    :param description: resource's description
    :type description: str
    :returns: newly created resource object
    :rtype: Resource
    """
    if folder:
        folder = utils.map_path_to_folder_id(folder_path=folder, ro_identifier=identifier)
    return Resource.Resource(ro_id=identifier, source="internal", resource_type=res_type,
                             file_path=file_path, title=title, folder=folder, description=description,
                             post_request=True)


def ros_add_external_resource(identifier, res_type, input_url, title=None, folder=None, description=None):
    """
    Function that adds external resource to the specific research object.

    .. seealso::
        :func:`~list_valid_resource_types`

    .. note::
        The newly created resource object will return a Python object that has its own set of methods
        and attributes. You may want to assign it to a variable to make it easy to work with.
        For example: ``my_res = ros_add_external_resource(**your set of params)``

    :param identifier: research object's identifier
    :type identifier: str
    :param res_type: type of resource
    :type res_type: str
    :param input_url: resource's url
    :type input_url: str
    :param title: resource's title, optional
    :type title: str
    :param folder: folder's path, optional
    :type folder: str
    :param description: resource's description
    :type description: str
    :returns: newly created resource object
    :rtype: Resource
    """
    if folder:
        folder = utils.map_path_to_folder_id(folder_path=folder, ro_identifier=identifier)
    return Resource.Resource(ro_id=identifier, source="external", resource_type=res_type,
                             input_url=input_url, title=title, folder=folder, description=description,
                             post_request=True)


@validate_authentication_token
def ros_add_triple(the_subject, the_predicate, the_object, annotation_id, object_class=None):
    """
    Function that adds triple to the specific annotation.

    .. seealso::
        :func:`~list_triple_object_classes`

    :param the_subject: triple's subject
    :type the_subject: str
    :param the_predicate: triple's predicate
    :type the_predicate: str
    :param the_object: triple's object
    :type the_object: str
    :param annotation_id: annotation's identifier
    :type annotation_id: str
    :param object_class: object's class, optional
    :type object_class: str
    :returns: response content from the API
    :rtype: dict
    """
    if object_class:
        try:
            valid_object_classes = set(list_triple_object_classes())
            verified_object_classes = utils.validate_against_different_formats(input_value=object_class,
                                                                               valid_value_set=valid_object_classes)
            # checking if set contains at least one element
            if len(verified_object_classes):
                # expected behaviour, only one value is correct
                object_class = verified_object_classes[0]
            else:
                # else leaving it empty
                object_class = None
        except Exception as e:
            msg = f"Couldn't validate object_class value! Leaving it empty!"
            print(msg)
            print(e)
            object_class = None
    url = settings.API_URL + "triples/"
    data = {"subject": the_subject,
            "predicate": the_predicate,
            "object": the_object,
            "object_class": object_class,
            "annotation": annotation_id}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content


@validate_authentication_token
def ros_set_authors(identifier, agents):
    """
    Function that sets authors to a specific research object.

    .. note::
        The order in which agents are provided as input is preserved in the API!

    .. seealso::
        The template for providing data for non-existing users is as follows:
        {"agent_type": "user", "display_name": "example_display_name", "email":"example_email",
        "orcid_id":"example_orcid_id", "affiliation": "example_affiliation"}

    :param identifier: research object's identifier
    :type identifier: str
    :param agents: usernames representing authors, if one doesn't exist it will be automatically created
    :type agents: list
    :returns: response content from the API
    :rtype: dict
    """
    if not isinstance(agents, list):
        msg = f"agents parameter has to be a list type, not a {type(agents)}"
        raise SystemExit(msg)
    validated_agents = utils.list_validated_agents(agents=agents, allow_org=False)
    if not validated_agents:
        msg = "At least one valid agent has to be provided!"
        raise SystemExit(msg)
    url = settings.API_URL + f"ros/{identifier}/authors/"
    data = {"ro": identifier,
            "agents": validated_agents}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content


@validate_authentication_token
def ros_set_contributors(identifier, agents):
    """
    Function that sets contributor to a specific research object.

    .. note::
        The order in which agents are provided as input is preserved in the API!

    .. seealso::
        The template for providing data for non-existing users is as follows:
        {"agent_type": "user", "display_name": "example_display_name", "email":"example_email",
        "orcid_id":"example_orcid_id", "affiliation": "example_affiliation"}

    :param identifier: research object's identifier
    :type identifier: str
    :param agents: usernames representing contributors, if one doesn't exist it will be automatically created
    :type agents: list
    :returns: response content from the API
    :rtype: dict
    """
    if not isinstance(agents, list):
        msg = f"agents parameter has to be a list type, not a {type(agents)}"
        raise SystemExit(msg)
    validated_agents = utils.list_validated_agents(agents=agents, allow_org=False)
    if not validated_agents:
        msg = "At least one valid agent has to be provided!"
        raise SystemExit(msg)
    if not isinstance(agents, list):
        msg = f"agents parameter has to be a list type, not a {type(agents)}"
        raise SystemExit(msg)
    url = settings.API_URL + f"ros/{identifier}/contributors/"
    data = {"ro": identifier,
            "agents": validated_agents}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content


@validate_authentication_token
def ros_set_publishers(identifier, agents):
    """
    Function that sets publishers to a specific research object.

    .. note::
        The order in which agents are provided as input is preserved in the API!

    .. seealso::
        The template for providing data for non-existing users/organizations is as follows:
        USER:
        {"agent_type": "user", "display_name": "example_display_name", "email":"example_email",
        "orcid_id":"example_orcid_id", "affiliation": "example_affiliation"}
        ORGANIZATION:
        {"agent_type": "organization", "display_name": "example_display_name", "email": "example_email",
        "organization_url": "example_url", "ror_identifier": "example_ror"}

    :param identifier: research object's identifier
    :type identifier: str
    :param agents: usernames/organizations representing publishers, if one doesn't exist it will be automatically created
    :type agents: list
    :returns: response content from the API
    :rtype: dict
    """
    if not isinstance(agents, list):
        msg = f"agents parameter has to be a list type, not a {type(agents)}"
        raise SystemExit(msg)
    validated_agents = utils.list_validated_agents(agents=agents, allow_org=True)
    if not validated_agents:
        msg = "At least one valid agent has to be provided!"
        raise SystemExit(msg)
    url = settings.API_URL + f"ros/{identifier}/publisher/"
    data = {"ro": identifier,
            "agents": validated_agents}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content


@validate_authentication_token
def ros_set_copyright_holders(identifier, agents):
    """
    Function that sets copyright holders to a specific Research Object.

    .. note::
        The order in which agents are provided as input is preserved in the API!

    .. seealso::
        The template for providing data for non-existing users/organizations is as follows:
        USER:
        {"agent_type": "user", "display_name": "example_display_name", "email":"example_email",
        "orcid_id":"example_orcid_id", "affiliation": "example_affiliation"}
        ORGANIZATION:
        {"agent_type": "organization", "display_name": "example_display_name", "email": "example_email",
        "organization_url": "example_url", "ror_identifier": "example_ror"}

    :param identifier: research object's identifier
    :type identifier: str
    :param agents: usernames/organizations representing holders, if one doesn't exist it will be automatically created
    :type agents: list
    :returns: response content from the API
    :rtype: dict
    """
    if not isinstance(agents, list):
        msg = f"agents parameter has to be a list type, not a {type(agents)}"
        raise SystemExit(msg)
    validated_agents = utils.list_validated_agents(agents=agents, allow_org=True)
    if not validated_agents:
        msg = "At least one valid agent has to be provided!"
        raise SystemExit(msg)
    url = settings.API_URL + f"ros/{identifier}/copyright/"
    data = {"ro": identifier,
            "agents": validated_agents}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content


@validate_authentication_token
def ros_add_funding(identifier, grant_identifier, grant_name, funder_name, grant_title=None, funder_doi=None):
    """
    Function that adds funding information to a specific research object.

    .. note::
        two auxiliary functions can be used to get some examples for funders and grants from the Zenodo database,
        respectively:
        :func:`~zenodo_list_funders`
        :func:`~zenodo_list_grants`
        check documentation of the above to get usage details

    :param identifier: research object's identifier
    :type identifier: str
    :param grant_identifier: grant's identifier
    :type grant_identifier: str
    :param grant_name: grant's name
    :type grant_name: str
    :param funder_name: funder's name
    :type funder_name: str
    :param grant_title: grant's title, optional
    :type grant_title: str
    :param funder_doi: funder's doi, optional
    :type funder_doi: str
    :returns: service identifier for the newly created funding
    :rtype: str
    """
    url = settings.API_URL + f"ros/{identifier}/fundings/"
    data = {"grant_identifier": grant_identifier,
            "grant_name": grant_name,
            "grant_title": grant_title,
            "funder_doi": funder_doi,
            "funder_name": funder_name}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content.get("identifier")


@validate_authentication_token
def ros_set_license(ros_id, license_id):
    """
    Function that sets license information associated with specific research object.

    .. seealso::
        :func:`~list_available_licenses`
        :func:`~list_custom_licenses`
        :func:`~add_custom_license`

    :param ros_id: research object's identifier
    :type ros_id: str
    :param license_id: license's identifier
    :type license_id: str
    :returns: response content from the API
    :rtype: dict
    """
    if not memo.licenses:
        memo.licenses = utils.get_available_licenses()
    if license_id not in memo.licenses:
        print("Incorrect license_id! You can check all available license options by running "
              " list_available_licenses().")
        return
    url = settings.API_URL + f"ros/{ros_id}/license/"
    data = {"identifier": license_id}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content


@validate_authentication_token
def ros_add_keywords(identifier, keywords):
    """
    Function that adds set of keywords to the specific research object.

    :param identifier: research object's identifier
    :type identifier: str
    :param keywords: list of keywords
    :type keywords: list
    :return: response content from the API
    :rtype: dict
    """
    if not isinstance(keywords, list):
        msg = f"keywords parameter has to be a list type, not a {type(keywords)}"
        raise SystemExit(msg)
    url = settings.API_URL + f"ros/{identifier}/keywords/"
    data = {"value": keywords, "append": True}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content


@validate_authentication_token
def ros_set_keywords(identifier, keywords):
    """
    Function that sets list of keywords for the specific research object.

    :param identifier: research object's identifier
    :type identifier: str
    :param keywords: list of keywords
    :type keywords: list
    :return: response content from the API
    :rtype: dict
    """
    if not isinstance(keywords, list):
        msg = f"keywords parameter has to be a list type, not a {type(keywords)}"
        raise SystemExit(msg)
    url = settings.API_URL + f"ros/{identifier}/keywords/"
    data = {"value": keywords}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content


@validate_authentication_token
def ros_make_golden(identifier):
    """
    Function that makes a specific research object golden.

    .. warning::
        Research object's completeness has to be 100% to make and keep it golden!

    .. seealso::
        :func:`~ros_completeness`

    :param identifier: research object's identifier
    :type identifier: str
    :returns: response containing keywords details
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/golden/"
    data = {"golden": True}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content


@validate_authentication_token
def ros_aggregate_datacube(identifier, dataset_id, product_id=None, product_media_type=None):
    """
    Function that aggregates datacube from adam platform to specific research object.

    :param identifier: research object's identifier
    :type: identifier: str
    :param dataset_id: dataset identifier
    :type dataset_id: str
    :param product_id: product identifier, optional
    :type product_id: str
    :param product_media_type: media type, has to be one of: image/tiff, image/png or application/xml, optional
    :returns: response from api
    :rtype: dict
    """
    if product_media_type:
        if product_media_type not in settings.ADAMPLATFORM_PRODUCT_MEDIA_TYPES:
            msg = f"Illegal option for product_media_type, has to be one of {settings.ADAMPLATFORM_PRODUCT_MEDIA_TYPES}!"
            raise SystemExit(msg)
    url = settings.API_URL + f"ros/{identifier}/aggregate_adam_platform_datacube/"
    data = {"dataset_identifier": dataset_id,
            "product_identifier": product_id,
            "product_media_type": product_media_type}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content


@validate_authentication_token
def ros_add_community(identifier, community_identifier):
    """
    Function that adds community to the specific research object.

    .. seealso::
        :func:`~list_communities`
        :func:`~ros_set_community`

    :param identifier: research object's identifier
    :type identifier: str
    :param community_identifier: community identifier
    :type community_identifier: str
    :returns: response content from the API
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/communities/"
    data = {"communities": community_identifier, "append": True}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content


@validate_authentication_token
def ros_set_community(identifier, community_identifier):
    """
    Function that sets community for the specific research object.

    .. seealso::
        :func:`~list_communities`
        :func:`~ros_add_community`

    :param identifier: research object's identifier
    :type identifier: str
    :param community_identifier: community identifier
    :type community_identifier: str
    :returns: response content from the API
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/communities/"
    data = {"communities": community_identifier}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content


@validate_authentication_token
def ros_add_main_entity(identifier, main_entity):
    """
    Function that associates main entity with specific Research Object.

    .. seealso::
        :func:`~list_valid_resource_types`

    :param identifier: research object's identifier
    :type identifier: str
    :param main_entity: main entity
    :type: main_entity: str
    :return: response content from the API
    :rtype: dict
    """
    acceptable_entities = rohub.list_valid_resource_types()
    if main_entity not in acceptable_entities:
        msg = ("Incorrect main entity value! You can check all available options by running "
              " list_valid_resource_types().")
        raise SystemExit(msg)
    url = settings.API_URL + f"ros/{identifier}/main_entity/"
    data = {"main_entity": main_entity}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content


@validate_authentication_token
def ros_add_sketch(identifier, path_to_sketch_file):
    """
    Function that adds sketch to a specific Research Object.

    :param identifier: research object's identifier
    :type identifier: str
    :param path_to_sketch_file: path to the existing file that will be uploaded as sketch
    :type: path_to_sketch_file: str
    :return: response content from the API
    :rtype: dict
    """
    if os.path.isfile(path_to_sketch_file):
        url = settings.API_URL + f"ros/{identifier}/sketch/"
        r = utils.post_request_with_file(url=url, file=path_to_sketch_file)
        content = r.json()
        return content
    else:
        msg = "File with provided path doesn't exist! Exiting..."
        raise SystemExit(msg)


###############################################################################
#              ROS upload methods.                                            #
###############################################################################


@validate_authentication_token
def ros_upload(path_to_zip):
    """
    Function that enables creating a new research object from the zip file.

    .. note::
        ZIP can be provided as a Research Object in RO-crate format (recommended) or in the legacy model format.
        Besides these two, it can also be a simple set of resources!

    .. seealso::
        | recommended RO exchange format: https://www.researchobject.org/ro-crate/1.1/
        | legacy model format: https://www.researchobject.org/specs/

    :param path_to_zip: path to the existing zip package
    :type path_to_zip: str
    :returns: response content from the API
    :rtype: dict
    """
    if os.path.isfile(path_to_zip):
        if zipfile.is_zipfile(path_to_zip):
            url = settings.API_URL + f"ros/upload/"
            r = utils.post_request_with_file(url=url, file=path_to_zip)
            content = r.json()
            job_id = content['identifier']
            if job_id:
                return is_job_success(job_id=job_id)
            else:
                msg = "Incorrect job response, couldn't validate if file was uploaded or not."
                raise SystemExit(msg)
        else:
            print("The file that was provided is not a real zip file! "
                  "Pleas try again with proper zip file.")
    else:
        print("Zip file doesn't exist! Please make sure passed path is correct!")


@validate_authentication_token
def ros_upload_resources(identifier, path_to_zip):
    """
    Function that enables creating a new resource from the zip file.

    :param identifier: research object's identifier
    :type identifier: str
    :param path_to_zip: path to the existing zip package
    :type path_to_zip: str
    :returns: response content from the API
    :rtype: dict
    """
    if os.path.isfile(path_to_zip):
        if zipfile.is_zipfile(path_to_zip):
            url = settings.API_URL + f"ros/{identifier}/resources/upload/"
            r = utils.post_request_with_file(url=url, file=path_to_zip)
            content = r.json()
            job_id = content['identifier']
            if job_id:
                return is_job_success(job_id=job_id)
            else:
                msg = "Incorrect job response, couldn't validate if file was uploaded or not."
                raise SystemExit(msg)
        else:
            print("The file that was provided is not a real zip file! "
                  "Pleas try again with proper zip file.")
    else:
        print("Zip file doesn't exist! Please make sure passed path is correct!")

###############################################################################
#              ROS delete methods.                                            #
###############################################################################


@validate_authentication_token
def ros_delete(identifier):
    """
    Function that deletes a specific research object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: response content from the API
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/"
    r = utils.delete_request(url=url)
    content = r.json()
    job_id = content['identifier']
    if job_id:
        return is_job_success(job_id=job_id)
    else:
        msg = "Incorrect job response, validation unsuccessful."
        raise SystemExit(msg)


@validate_authentication_token
def ros_delete_funding(identifier, funding_identifier):
    """
    Function that deletes specific funding associated with specific research object.

    .. seealso::
        :func:`~ros_list_fundings`

    :param identifier: research object's identifier
    :type identifier: str
    :param funding_identifier: funding's identifier
    :type funding_identifier: str
    :returns: None
    :rtype: None
    """
    url = settings.API_URL + f"ros/{identifier}/fundings/{funding_identifier}/"
    r = utils.delete_request(url=url)
    if r.status_code != 204:
        content = r.json()
        return content
    else:
        print("Funding successfully deleted!")
        return


@validate_authentication_token
def ros_delete_license(identifier):
    """
    Function that deletes association between license and specific research object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: None
    :rtype: None
    """
    url = settings.API_URL + f"ros/{identifier}/license/"
    r = utils.delete_request(url=url)
    if r.status_code != 204:
        content = r.json()
        return content
    else:
        print("License successfully deleted!")
        return


@validate_authentication_token
def ros_delete_keywords(identifier):
    """
    Function that deletes all keywords associated with specific research object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: None
    :rtype: None
    """
    url = settings.API_URL + f"ros/{identifier}/keywords/"
    r = utils.delete_request(url=url)
    if r.status_code != 204:
        content = r.json()
        return content
    else:
        print("Keywords successfully deleted!")
        return


@validate_authentication_token
def ros_undo_golden(identifier):
    """
    Function that makes specific research object stop being golden.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: None
    :rtype: None
    """
    url = settings.API_URL + f"ros/{identifier}/golden/"
    r = utils.delete_request(url=url)
    if r.status_code != 204:
        content = r.json()
        return content
    else:
        print("Research Object is no longer golden!")
        return


@validate_authentication_token
def ros_delete_communities(identifier):
    """
    Function that deletes association between community/communities and research object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: None
    :rtype: None
    """
    url = settings.API_URL + f"ros/{identifier}/communities/"
    r = utils.delete_request(url=url)
    if r.status_code != 204:
        content = r.json()
        return content
    else:
        print("Communities erased from the research object!")
        return


@validate_authentication_token
def ros_delete_main_entity(identifier):
    """
    Function that deletes main entity association for a specific Research Object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: None
    :rtype: None
    """
    url = settings.API_URL + f"ros/{identifier}/main_entity/"
    r = utils.delete_request(url=url)
    if r.status_code != 204:
        content = r.json()
        return content
    else:
        print("Main entity erased from the research object!")
        return


@validate_authentication_token
def ros_delete_editors(identifier):
    """
    Function that deletes editors association from a specific Research Object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: response containing details
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/delete_editors/"
    r = utils.post_request_no_data(url=url)
    content = r.json()
    return content


@validate_authentication_token
def ros_delete_readers(identifier):
    """
    Function that deletes readers association from a specific Research Object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: response containing details
    :rtype: dict
    """
    url = settings.API_URL + f"ros/{identifier}/delete_readers/"
    r = utils.post_request_no_data(url=url)
    content = r.json()
    return content


@validate_authentication_token
def ros_delete_authors(identifier):
    """
    Function that deletes authors association for a specific Research Object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: None
    :rtype: None
    """
    url = settings.API_URL + f"ros/{identifier}/authors/"
    r = utils.delete_request(url=url)
    if r.status_code != 204:
        content = r.json()
        return content
    else:
        print("Authors erased from the research object!")
        return


@validate_authentication_token
def ros_delete_contributors(identifier):
    """
    Function that deletes contributors association for a specific Research Object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: None
    :rtype: None
    """
    url = settings.API_URL + f"ros/{identifier}/contributors/"
    r = utils.delete_request(url=url)
    if r.status_code != 204:
        content = r.json()
        return content
    else:
        print("Contributors erased from the research object!")
        return


@validate_authentication_token
def ros_delete_publishers(identifier):
    """
    Function that deletes publishers association for a specific Research Object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: None
    :rtype: None
    """
    url = settings.API_URL + f"ros/{identifier}/publisher/"
    r = utils.delete_request(url=url)
    if r.status_code != 204:
        content = r.json()
        return content
    else:
        print("Publishers erased from the research object!")
        return


@validate_authentication_token
def ros_delete_copyright_holders(identifier):
    """
    Function that deletes copyright holders association for a specific Research Object.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: None
    :rtype: None
    """
    url = settings.API_URL + f"ros/{identifier}/copyright/"
    r = utils.delete_request(url=url)
    if r.status_code != 204:
        content = r.json()
        return content
    else:
        print("Copyright holders erased from the research object!")
        return

###############################################################################
#              ROS put methods.                                               #
###############################################################################


@validate_authentication_token
def ros_update(identifier, title, research_areas, description=None, access_mode=None,
               ros_type=None, template=None, owner=None, editors=None,
               readers=None, creation_mode=None):
    """
    Function that updates specific research object.

    .. seealso::
        :func:`~list_valid_research_areas`
        :func:`~list_valid_access_modes`
        :func:`~list_valid_ros_types`
        :func:`~list_valid_templates`
        :func:`~list_valid_creation_modes`

    :param identifier: research object's identifier
    :type identifier: str
    :param title: title of your research object
    :type title: str
    :param research_areas: research areas associated with your research object
    :type research_areas: list
    :param description: description of your research object, optional
    :type description: str
    :param access_mode: research object's access mode, optional
    :type access_mode: str
    :param ros_type: research object's type, optional
    :type ros_type: str
    :param template: research object's template, optional
    :type template: str
    :param owner: research object's owner, optional
    :type owner: str
    :param editors: research object's editors, optional
    :type editors: list
    :param readers: research object's readers, optional
    :type readers: list
    :param creation_mode: research object's creation mode, optional
    :returns: response content from the API
    :rtype: dict
    """
    data = {"title": title,
            "research_areas": research_areas,
            "description": description,
            "access_mode": access_mode,
            "type": ros_type,
            "template": template,
            "owner": owner,
            "editors": editors,
            "readers": readers,
            "creation_mode": creation_mode}
    data = {key: value for key, value in data.items() if value is not None}
    print(data)
    url = settings.API_URL + f"ros/{identifier}/"
    r = utils.put_request(url=url, data=data, use_token=True)
    content = r.json()
    return content


@validate_authentication_token
def ros_update_funding(identifier, funding_identifier, grant_identifier=None, grant_name=None,
                       grant_title=None, funder_doi=None, funder_name=None):
    """
    Function that updates specific funding associated with specific research object.

    .. seealso::
        :func:`~ros_list_fundings`

    :param identifier: research object's identifier
    :type identifier: str
    :param funding_identifier: funding's identifier
    :type funding_identifier: str
    :param grant_identifier: grant's identifier, optional
    :type grant_identifier: str
    :param grant_name: grant's name, optional
    :type grant_name: str
    :param funder_name: funder's name, optional
    :type funder_name: str
    :param grant_title: grant's title, optional
    :type grant_title: str
    :param funder_doi: funder's doi, optional
    :type funder_doi: str
    :returns: response content from the API
    :rtype: dict
    """
    data = {"grant_identifier": grant_identifier,
            "grant_name": grant_name,
            "grant_title": grant_title,
            "funder_doi": funder_doi,
            "funder_name": funder_name}
    data = {key: value for key, value in data.items() if value is not None}
    url = settings.API_URL + f"ros/{identifier}/fundings/{funding_identifier}/"
    r = utils.patch_request(url=url, data=data)
    content = r.json()
    return content

###############################################################################
#              Resource main methods.                                         #
###############################################################################


@validate_authentication_token
def resource_find(source=None, search=None):
    """
    Function that finds a specific resource against the provided query.

    :param source: source of the resource, can be either external or internal or empty to search in both sources, optional
    :type: source: str
    :param search: phrase to search against, optional
    :type: str
    :returns: table containing selected information about the research object/objects
    :rtype: Panda's DataFrame
    """
    url = settings.API_URL + f"search/resources/"
    if any([source, search]):
        if source == "external":
            params = {"search": search,
                      "local": False}
        elif source == "internal":
            params = {"search": search,
                      "local": True}
        else:
            params = {"search": search}
        r = utils.get_request_with_params(url=url, params=params, use_token=True)
    else:
        r = utils.get_request(url=url, use_token=True)
    content = r.json()
    results = content.get("results")
    while content["next"]:
        r = utils.get_request(url=content["next"])
        content = r.json()
        results.extend(content.get("results"))
    df = pd.DataFrame(results)
    if not df.empty:
        selected_columns = ["identifier", "type", "title", "description", "url", "filename",
                            "path", "size", "creator", "created", "modified", "download_url"]
        df.drop(df.columns.difference(selected_columns), axis=1, inplace=True)
        df["source"] = np.where(df["url"].isna(), "internal", "external")
        column_sequence = ["identifier", "type", "source", "title", "description", "url", "filename",
                           "path", "size", "creator", "created", "modified", "download_url"]
        df = df.reindex(columns=column_sequence)
    return df


@validate_authentication_token
def resource_search_using_id(identifier):
    """
    Function that displays details acquired from the API for the specific resource.

    :param identifier: resource's identifier
    :type identifier: str
    :returns: response content from the API
    :rtype: dict
    """
    url = settings.API_URL + f"resources/{identifier}/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    return content


def resource_load(identifier):
    """
    Function that loads an existing resource.

    :param identifier: resource's identifier
    :type identifier: str
    :returns: loaded resource
    :rtype: Resource
    """
    return Resource.Resource(identifier=identifier, post_request=False)


@validate_authentication_token
def resource_assign_doi(identifier, external_doi=None):
    """
    Function that assigns doi to a specific resource.

    .. note::
        If external_doi value was provided it will be used as doi, otherwise the system
        will automatically generate and assign doi!

    :param identifier: resource's identifier
    :type identifier: str
    :param external_doi: value for the external, existing doi, optional
    :type external_doi: str
    :returns: doi
    :rtype: str
    """
    if external_doi:
        data = {"external_doi": external_doi}
    else:
        data = {"create_doi": True}
    url = settings.API_URL + f"resources/{identifier}/doi/"
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content.get("doi")


@validate_authentication_token
def resource_download(identifier, resource_filename=None, path=None, redirect=False):
    """
    Function that acquires a specific resource into local file storage.

    :param identifier: resource's identifier
    :type identifier: str
    :param resource_filename: resource's full filename (with extension), required when redirect is False
    :type resource_filename: str
    :param path: path where file should be downloaded, optional - current working dir is the default!
    :type path: str
    :param redirect: if True the direct EGI link will be generated and passed instead of downloading the resource
                    (works only with Jupyter Notebook, Data Cube Collection and Data Cube Product types of resource)
    :returns: full path to the acquired resource
    :rtype: str
    """
    url = settings.API_URL + f"resources/{identifier}/download/"
    if redirect:
        if utils.validate_if_resource_can_be_redirected(resource_id=identifier):
            #params = {"redirect": True}
            url = settings.API_URL + f"resources/{identifier}/open/"
            r = utils.get_request(url=url, use_token=True)
            return r.text
        else:
            msg = f"Aborting... redirect option is available only for the following resource types: " \
                  f"{settings.REDIRECT_RESOURCE_TYPES}!"
            print(msg)
            return
    else:
        if not resource_filename:
            msg = "resource_filename is required when redirect is not used. " \
                  "Please provided the filename with extension."
            raise SystemExit(msg)
        if path:
            os.makedirs(path, exist_ok=True)
            full_path = os.path.join(path, resource_filename)
        else:
            full_path = os.path.join(resource_filename)
        r = utils.get_request(url=url)
        content = r.content
        with open(full_path, 'wb') as out_file:
            out_file.write(content)
            if path:
                print(f"File was successfully downloaded into {path}.")
            else:
                print(f"File was successfully downloaded.")
            return full_path


@validate_authentication_token
def resource_set_license(res_id, license_id):
    """
    Function that sets license information associated with specific research object.

    .. seealso::
        :func:`~list_available_licenses`
        :func:`~list_custom_licenses`
        :func:`~add_custom_license`

    :param res_id: resource identifier
    :type res_id: str
    :param license_id: license's identifier
    :type license_id: str
    :returns: response content from the API
    :rtype: dict
    """
    if not memo.licenses:
        memo.licenses = utils.get_available_licenses()
    if license_id not in memo.licenses:
        print("Incorrect license_id! You can check all available license options by running "
              " list_available_licenses().")
        return
    url = settings.API_URL + f"resources/{res_id}/license/"
    data = {"identifier": license_id}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content


@validate_authentication_token
def resource_list_license(identifier):
    """
    Function that lists license associated with certain research object.

    :param identifier: resource identifier.
    :type identifier: str
    :returns: response containing license details
    :rtype: dict
    """
    url = settings.API_URL + f"resources/{identifier}/license/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    return content


def resource_list_keywords(identifier):
    """
    Function that shows list of keywords for specific Resource

    :param identifier: resource identifier
    :type identifier: str
    :returns: response containing keywords details
    :rtype: dict
    """
    url = settings.API_URL + f"resources/{identifier}/keywords/"
    r = utils.get_request(url=url, use_token=False)
    content = r.json()
    return content


@validate_authentication_token
def resource_add_keywords(identifier, keywords):
    """
    Function that adds set of keywords to the specific resource.

    :param identifier: resource identifier
    :type identifier: str
    :param keywords: list of keywords
    :type keywords: list
    :returns: response content from the API
    :rtype: dict
    """
    if not isinstance(keywords, list):
        msg = f"keywords parameter has to be a list type, not a {type(keywords)}"
        raise SystemExit(msg)
    url = settings.API_URL + f"resources/{identifier}/keywords/"
    data = {"value": keywords, "append": True}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content


@validate_authentication_token
def resource_set_keywords(identifier, keywords):
    """
    Function that sets list of keywords for the specific resource.

    :param identifier: research object's identifier
    :type identifier: str
    :param keywords: list of keywords
    :type keywords: list
    :returns: response content from the API
    :rtype: dict
    """
    if not isinstance(keywords, list):
        msg = f"keywords parameter has to be a list type, not a {type(keywords)}"
        raise SystemExit(msg)
    url = settings.API_URL + f"resources/{identifier}/keywords/"
    data = {"value": keywords}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content

###############################################################################
#              Resource delete methods.                                       #
###############################################################################


@validate_authentication_token
def resource_delete(identifier):
    """
    Function that deletes a resource associated with a specific research object.

    :param identifier: resource's identifier
    :type identifier: str
    :returns: None
    :rtype: None
    """
    url = settings.API_URL + f"resources/{identifier}/"
    r = utils.delete_request(url=url)
    if r.status_code != 204:
        content = r.json()
        return content
    else:
        print("Resource successfully deleted!")
        return


@validate_authentication_token
def resource_delete_license(identifier):
    """
    Function that deletes association between license and specific resource.

    :param identifier: research object's identifier
    :type identifier: str
    :returns: None
    :rtype: None
    """
    url = settings.API_URL + f"resources/{identifier}/license/"
    r = utils.delete_request(url=url)
    if r.status_code != 204:
        content = r.json()
        return content
    else:
        print("License successfully deleted!")
        return


@validate_authentication_token
def resource_delete_keywords(identifier):
    """
    Function that deletes all keywords associated with specific resource.

    :param identifier: resource identifier
    :type identifier: str
    :returns: None
    :rtype: None
    """
    url = settings.API_URL + f"resources/{identifier}/keywords/"
    r = utils.delete_request(url=url)
    if r.status_code != 204:
        content = r.json()
        return content
    else:
        print("Keywords successfully deleted!")
        return

###############################################################################
#              Resource put methods.                                          #
###############################################################################


@validate_authentication_token
def resource_update_metadata(identifier, ro_id=None, res_type=None, title=None,
                             folder=None, description=None):
    """
    Function that updates metadata for a specific resource.

    .. seealso::
        :func:`~list_valid_resource_types`

    .. note::
        to move back a resource to the "Home" directory set folder = "/"

    :param identifier: resource's identifier
    :type identifier: str
    :param ro_id: research object's identifier, required only if folder was provided!
    :type ro_id: str
    :param res_type: resource's type, optional
    :type res_type: str
    :param title: resource's title, optional
    :type title: str
    :param folder: folder's path, optional
    :type folder: str
    :param description: resource's description, optional
    :type description: str
    :returns: response content from the API
    :rtype: dict
    """
    if res_type:
        try:
            valid_resource_types = set(list_valid_resource_types())
            verified_res_type = utils.validate_against_different_formats(input_value=res_type,
                                                                         valid_value_set=valid_resource_types)
            # checking if set contains at least one element
            if len(verified_res_type):
                # expected behaviour, only one value is correct
                res_type = verified_res_type[0]
            else:
                msg = f"Incorrect resource type. Must be one of: {valid_resource_types}"
                raise SystemExit(msg)
        except KeyError:
            msg = "Something went wrong and we couldn't validate the resource type."
            print(msg)
    url = settings.API_URL + f"resources/{identifier}/"
    if folder:
        if folder == "/":
            data = {"type": res_type if res_type else None,
                    "title": title,
                    "description": description,
                    "folder": folder}
            data = {key: value for key, value in data.items() if value is not None}
            data["folder"] = None
            r = utils.patch_request_json_payload(url=url, data=data)
            content = r.json()
            return content
        else:
            folder = utils.map_path_to_folder_id(folder_path=folder, ro_identifier=ro_id)
    data = {"type": res_type if res_type else None,
            "title": title,
            "description": description,
            "folder": folder}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.patch_request(url=url, data=data)
    content = r.json()
    return content


@validate_authentication_token
def resource_update_content(identifier, input_url=None, file_path=None):
    """
    Function that updates content of specific resource.

    .. note::
        input_url is required for updating external resource, and file_path
        is in case of internal one. At least one of them has to be provided!

    .. warning::
        The resource content will be overwritten!

    :param identifier: resource's identifier
    :type identifier: str
    :param input_url: url to the external resource, optional
    :type input_url: str
    :param file_path: path to the internal resource, optional
    :type file_path: str
    :returns: response content from the API
    :rtype: dict
    """
    if not any([input_url, file_path]):
        msg = "One of arguments: input_url, file_path is required! File_path should be provided" \
              " for the internal resource, and input_url for the external."
        raise SystemExit(msg)
    if input_url and file_path:
        msg = "Incorrect usage: only one of input_url, file_path arguments should be provided!"
        raise SystemExit(msg)
    url = settings.API_URL + f"resources/{identifier}/"
    if file_path:
        if not os.path.isfile(file_path):
            msg = "ERROR: file_path doesn't point to an existing file!"
            raise SystemExit(msg)
        r = utils.patch_request_with_file_no_data(url=url, file=file_path)
    else:
        data = {"url": input_url}
        r = utils.patch_request(url=url, data=data)
    content = r.json()
    return content

###############################################################################
#              Folder methods.                                                #
###############################################################################


def folder_load(identifier):
    """
    Function that loads an existing folder.

    :param identifier: folder's identifier
    :type identifier: str
    :returns: loaded folder object
    :rtype: Folder
    """
    return Folder.Folder(identifier=identifier, post_request=False)


@validate_authentication_token
def folder_search_using_id(folder_identifier):
    """
    Function for displaying all details associated with a specific folder.

    :param folder_identifier: folder's identifier
    :type folder_identifier: str
    :returns: response content from the API
    :rtype: dict
    """
    url = settings.API_URL + f"folders/{folder_identifier}/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    return content


@validate_authentication_token
def folder_update(identifier, name, ro_identifier, description=None, parent_folder=None):
    """
    Function that updates metadata related to a specific folder.

    :param identifier: folder's identifier
    :type identifier: str
    :param name: folder's name
    :type name: str
    :param ro_identifier: identifier for research object that is associated with requested folder
    :type ro_identifier: str
    :param description: folder's description, optional
    :type description: str
    :param parent_folder: parent folder path, optional
    :type parent_folder: str
    :returns: response content from the API
    :rtype: dict
    """
    data = {"name": name,
            "ro": ro_identifier,
            "description": description,
            "parent_folder": parent_folder}
    data = {key: value for key, value in data.items() if value is not None}
    url = settings.API_URL + f"folders/{identifier}/"
    r = utils.put_request(url=url, data=data, use_token=True)
    content = r.json()
    return content


@validate_authentication_token
def folder_delete(folder_identifier):
    """
    Function that deletes a folder associated with specific research object.

    :param folder_identifier: folder's identifier
    :type folder_identifier: str
    :returns: None
    :rtype: None
    """
    url = settings.API_URL + f"folders/{folder_identifier}/"
    r = utils.delete_request(url=url)
    if r.status_code != 204:
        content = r.json()
        return content
    else:
        print("Folder successfully deleted!")
        return

###############################################################################
#              Annotation methods.                                            #
###############################################################################


@validate_authentication_token
def annotation_delete(annotation_identifier):
    """
    Function that deletes an annotation associated with specific research object.

    :param annotation_identifier: annotation's identifier
    :type annotation_identifier: str
    :returns: None
    :rtype: None
    """
    url = settings.API_URL + f"annotations/{annotation_identifier}/"
    r = utils.delete_request(url=url)
    if r.status_code != 204:
        content = r.json()
        return content
    else:
        print("Annotation successfully deleted!")
        return

###############################################################################
#              USER methods.                                                  #
###############################################################################


@validate_authentication_token
def users_find(search=None):
    """
    Function that finds a user against the provided query.

    .. warning::
        if no query provided then all users will be retrieved!

    :param search: query, optional
    :type search: str
    :returns: table containing selected information about users
    :rtype: Panda's DataFrame
    """
    url = settings.API_URL + f"search/users/"
    if search:
        params = {"search": search}
        r = utils.get_request_with_params(url=url, params=params)
    else:
        r = utils.get_request(url=url)
    content = r.json()
    results = content.get("results")
    while content["next"]:
        r = utils.get_request(url=content["next"])
        content = r.json()
        results.extend(content.get("results"))
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.loc[df["other"] == False]
        selected_columns = ['identifier', 'username', 'display_name', 'affiliation',
                            'description', 'areas_of_interest', 'orcid_identifier', 'external']
        df.drop(df.columns.difference(selected_columns), axis=1, inplace=True)
    return df


def show_user_id(username=None):
    """
    Function that displays user's identifier based on their username.

    :param username: username, optional - if not provided id for currently logged user will be retrieved
    :type username: str
    :returns: user's identifier
    :rtype: str
    """
    if not username:
        url = settings.API_URL + "users/whoami/"
        r = utils.get_request(url=url, use_token=True)
        content = r.json()
        try:
            user_id = content["identifier"]
        except KeyError as e:
            print("Ups... something went wrong. Couldn't read user's id from response.")
            print(e)
            return
    else:
        user_id = utils.search_for_user_id(username=username)
    return user_id


###############################################################################
#              EXTERNAL USER methods.                                         #
###############################################################################


@validate_authentication_token
def external_user_add(display_name, email=None, orcid_id=None, affiliation=None):
    """
    Function that creates an external user.

    .. note::
        Either email or orcid_id has to be provided in order to create new external user!

    :param display_name: displayed name for the user
    :type display_name: str
    :param email: user's email address, optional
    :type email: str
    :param orcid_id: user's orcid_id, optional
    :type orcid_id: str
    :param affiliation: user's affiliation, optional
    :type affiliation: str
    :returns: internal identifier for the newly created user
    :rtype: str
    """
    if not email and not orcid_id:
        msg = "Illegal usage: either email or orcid_id has to be provided in order to create user!"
        raise SystemExit(msg)
    url = settings.API_URL + f"external_users/"
    data = {"user_id": utils.generate_orcid_url(orcid_id) if orcid_id else email,
            "display_name": display_name,
            "email": email,
            "orcid_identifier": orcid_id,
            "affiliation": affiliation}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    identifier = content["identifier"]
    print(f"User successfully created with internal id: {identifier}!")
    return identifier

###############################################################################
#              ORGANIZATIONS methods.                                         #
###############################################################################


@validate_authentication_token
def organization_add(display_name, email=None, organization_url=None,
                     ror_identifier=None):
    """
    Function that creates a new organization.

    .. note::
        Either email or ror_identifier has to be provided in order to create new organization!

    :param display_name: displayed name for the organization
    :type display_name: str
    :param email: organization's email address, optional
    :type email: str
    :param organization_url: organization's url, optional
    :type organization_url: str
    :param ror_identifier: organization's ror identifier, optional
    :type ror_identifier: str
    :returns: internal identifier for the newly created organization
    :rtype: str
    """
    if not email and not ror_identifier:
        msg = "Illegal usage: either email or ror_identifier has to be provided in order to create organization!"
        raise SystemExit(msg)
    url = settings.API_URL + f"organizations/"
    data = {"organization_id": utils.generate_ror_url(ror_identifier) if ror_identifier else email,
            "display_name": display_name,
            "email": email,
            "url": organization_url,
            "ror_identifier": ror_identifier}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    identifier = content["identifier"]
    print(f"Organization successfully created with internal id: {identifier}!")
    return identifier


@validate_authentication_token
def organizations_find(search=None):
    """
    Function that finds organization against the provided query.

    .. warning::
        if no query provided then all organizations will be retrieved!

    :param search: query, optional
    :type search: str
    :returns: table containing selected information about organizations
    :rtype: Panda's DataFrame
    """
    url = settings.API_URL + f"search/organizations/"
    if search:
        params = {"search": search}
        r = utils.get_request_with_params(url=url, params=params)
    else:
        r = utils.get_request(url=url)
    content = r.json()
    results = content.get("results")
    while content["next"]:
        r = utils.get_request(url=content["next"])
        content = r.json()
        results.extend(content.get("results"))
    df = pd.DataFrame(results)
    return df

###############################################################################
#              Auxiliary methods.                                             #
###############################################################################


def zenodo_list_funders(query):
    """
    Function that displays list of funders from the Zenodo database against user's query.

    .. note::
        Zenodo performs tight matching, so one has to be specific with the query value.

    .. warning::
        Zenodo limits number of records to 10 000. Be aware of that! The table will include maximum
        10 000 rows no matter how many results there is in the whole Zenodo database!
        One can try to restrict number of results by making query more specific.

    :param query: query to search against
    :type query: str
    :returns: table containing selected information about funders
    :rtype: Panda's DataFrame
    """
    base_url = settings.ZENODO_FUNDERS_URL

    url = base_url + f"?q={query}&size=1000"
    r = utils.get_request(url=url, use_token=False)
    content = r.json()
    results = []

    def _parse_data_from_single_page(api_json):
        for hit in api_json.get("hits").get("hits"):
            identifiers = hit.get("identifiers")
            title = hit.get("name")
            types = hit.get("types")
            country = hit.get("country")
            created = hit.get("created")
            updated = hit.get("updated")
            results.extend([{
                "identifiers": identifiers,
                "title": title,
                "types": types,
                "country": country,
                "created": created,
                "updated": updated,
            }])
    _parse_data_from_single_page(api_json=content)
    next_page_url = content.get("links").get("next")
    while next_page_url:
        r = utils.get_request(url=next_page_url)
        content = r.json()
        _parse_data_from_single_page(api_json=content)
        next_page_url = content.get("links").get("next")
    df = pd.DataFrame(results)
    return df


def zenodo_list_grants(query):
    """
    Function that displays list of grants from the Zenodo database against user's query.

    .. note::
        Zenodo performs tight matching, so one has to be specific with the query value.

    .. warning::
        Zenodo limits number of records to 10 000. Be aware of that! The table will include maximum
        10 000 rows no matter how many results there is in the whole Zenodo database!
        One can try to restrict number of results by making query more specific.

    :param query: query to search against
    :type query: str
    :returns: table containing selected information about grants
    :rtype: Panda's DataFrame
    """
    base_url = settings.ZENODO_GRANTS_URL
    url = base_url + f"?q={query}&size=1000"
    r = utils.get_request(url=url, use_token=False)
    content = r.json()
    results = []

    def _parse_data_from_single_page(api_json):
        for hit in api_json.get("hits").get("hits"):
            identifier = hit.get("id")
            title = hit.get("title")
            funder_id = hit.get("funder").get("id")
            funder_name = hit.get("funder").get("name")
            created = hit.get("created")
            updated = hit.get("updated")
            results.extend([{
                "identifier": identifier,
                "title": title,
                "funder_doi": funder_id,
                "funder_name": funder_name,
                "created": created,
                "updated": updated,
            }])
    _parse_data_from_single_page(api_json=content)
    next_page_url = content.get("links").get("next")
    while next_page_url:
        r = utils.get_request(url=next_page_url)
        content = r.json()
        _parse_data_from_single_page(api_json=content)
        next_page_url = content.get("links").get("next")
    df = pd.DataFrame(results)
    return df


def list_available_licenses():
    """
    Function that lists all available options for the license identifier.

    :returns: all available license identifiers
    :rtype: list
    """
    if not memo.licenses:
        memo.licenses = utils.get_available_licenses()
    return memo.licenses


def list_valid_research_areas():
    """
    Function that lists all valid research areas.

    :returns: valid research areas
    :rtype: list
    """
    if not memo.research_areas:
        r = utils.get_request(url=settings.API_URL + "research-areas/")
        if r:
            content = r.json()
            results = content.get("results")
            while content["next"]:
                r = utils.get_request(url=content["next"])
                content = r.json()
                results.extend(content.get("results"))
            for result in results:
                memo.research_areas.append(result['name'])
        else:
            msg = "Something went wrong... Couldn't access valid research areas. Please try again."
            print(msg)
            return
    return memo.research_areas


def list_valid_access_modes():
    """
    Function for listing all valid access modes.

    :returns: valid access modes
    :rtype: list
    """
    if not memo.service_enums:
        memo.service_enums = utils.get_available_enums()
    return memo.service_enums["ro_access_mode"]


def list_valid_ros_types():
    """
    Function that lists all valid ros types.

    :returns: valid ros types
    :rtype: list
    """
    if not memo.service_enums:
        memo.service_enums = utils.get_available_enums()
    return memo.service_enums["ro_type"]


def list_valid_templates():
    """
    Function that lists all valid templates.

    :returns: valid templates
    :rtype: list
    """
    if not memo.service_enums:
        memo.service_enums = utils.get_available_enums()
    return memo.service_enums["ro_template"]


def list_valid_creation_modes():
    """
    Function that lists all valid creation modes.

    :returns: valid creation modes
    :rtype: list
    """
    if not memo.service_enums:
        memo.service_enums = utils.get_available_enums()
    return memo.service_enums["ro_creation_mode"]


def list_valid_resource_types():
    """
    Function for lists all valid resource types.

    :returns: valid resource types
    :rtype: list
    """
    if not memo.service_enums:
        memo.service_enums = utils.get_available_enums()
    return memo.service_enums["resource_type"]


def list_valid_publication_services():
    """
    Function that lists all valid publication services.

    :returns: valid publication services
    :rtype: list
    """
    if not memo.service_enums:
        memo.service_enums = utils.get_available_enums()
    return memo.service_enums["publication_service"]


def list_valid_license_status():
    """
    Function that lists all valid statuses for the custom license.

    :returns: valid license statuses
    :rtype: list
    """
    if not memo.service_enums:
        memo.service_enums = utils.get_available_enums()
    return memo.service_enums["license_status"]


def list_triple_object_classes():
    """
    Function that lists all valid triple object classes.

    :returns: valid triple object classes
    :rtype: list
    """
    if not memo.service_enums:
        memo.service_enums = utils.get_available_enums()
    return memo.service_enums["triple_object_class"]


@validate_authentication_token
def list_custom_licenses(active_only=False):
    """
    Function that lists existing custom licenses.

    :param active_only: if True only active licenses will be listed, default is False
    :type active_only: bool
    :returns: existing custom licenses
    :rtype: list
    """
    url = settings.API_URL + f"custom-licenses/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    results = content.get("results")
    while content["next"]:
        r = utils.get_request(url=content["next"])
        content = r.json()
        results.extend(content.get("results"))
    if results:
        if active_only:
            active_only_results = [lice for lice in results if lice["status"] == "active"]
            return active_only_results
        return results
    else:
        msg = "Unexpected error. Couldn't obtain custom licenses results."
        print(msg)


@validate_authentication_token
def add_custom_license(identifier, title, status, license_url, description=None):
    """
    Function that adds a new custom license.

    .. seealso::
        :func:`~list_valid_license_status`

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
        valid_status = set(list_valid_license_status())
        verified_status = utils.validate_against_different_formats(input_value=status,
                                                                   valid_value_set=valid_status)
        # checking if set contains at least one element
        if len(verified_status):
            # expected behaviour, only one value is correct
            status = verified_status[0]
        else:
            msg = f"Incorrect resource type. Must be one of: {valid_status}"
            raise SystemExit(msg)
    except Exception as e:
        msg = "Unexpected error: couldn't validate license status value."
        print(msg)
        print(e)

    url = settings.API_URL + f"custom-licenses/"
    data = {"identifier": identifier,
            "title": title,
            "status": status,
            "url": license_url,
            "description": description}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content


@validate_authentication_token
def show_valid_type_matching_for_ros():
    """
    Function that displays valid pairs for ros_type and template.

    :returns: response content from the API
    :rtype: dict
    """
    url = settings.API_URL + f"ros/type_matching/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    return content


@validate_authentication_token
def list_communities():
    """
    Function that lists all existing communities.

    :returns: existing communities
    :rtype: list
    """
    url = settings.API_URL + f"communities/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    results = content.get("results")
    while content["next"]:
        r = utils.get_request(url=content["next"])
        content = r.json()
        results.extend(content.get("results"))
    if results:
        return results
    else:
        msg = "Unexpected error. Couldn't obtain any communities results."
        print(msg)


@validate_authentication_token
def create_community(name, description=None, email=None, community_url=None):
    """
    Function for creating a new community.

    .. seealso::
        :func:`~list_communities`

    :param name: name of the community
    :type: name: str
    :param description: description, optional
    :type: description: str
    :param email: community's email, optional
    :type: email: str
    :param community_url: associated url, optional
    :type community_url: str
    :returns: response content from the API
    :rtype: dict
    """
    url = settings.API_URL + f"communities/"
    data = {"name": name,
            "description": description,
            "email": email,
            "url": community_url}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content


@validate_authentication_token
def adam_platform_metadata_find(search=None):
    """
    Function that finds metadata from adam platform against the provided query.

    .. warning::
        if no query provided then all metadata will be retrieved!

    :param search: query, optional
    :type search: str
    :returns: table containing selected adam platform metadata
    :rtype: Panda's DataFrame
    """
    url = settings.API_URL + f"search/adam_platform_metadata/"
    if search:
        params = {"search": search}
        r = utils.get_request_with_params(url=url, params=params)
    else:
        r = utils.get_request(url=url)
    content = r.json()
    results = content.get("results")
    while content["next"]:
        r = utils.get_request(url=content["next"])
        content = r.json()
        results.extend(content.get("results"))
    df = pd.DataFrame(results)
    if not df.empty:
        selected_columns = ['identifier', 'dataset_identifier', 'product_identifier', 'product_file_name',
                            'urls', 'urls_text', 'wcs_identifier', 'metadata', 'created_on', 'modified_on', 'type',
                            'highlight', 'score']
        df.drop(df.columns.difference(selected_columns), axis=1, inplace=True)
    return df


@validate_authentication_token
def list_accepted_dmp_templates():
    """
    Function that lists all supported DMP templates.

    :returns: list containing all supported DMP templates
    :rtype: list
    """
    url = settings.API_URL + f"dmp/"
    r = utils.get_request(url=url, use_token=True)
    content = r.json()
    return content.get("accepted_dmp_templates")


@validate_authentication_token
def process_dmp_template(path_to_template_file):
    """
    Function for processing xml templates.

    :param path_to_template_file: path to the existing xml template
    :type: path_to_template_file: str
    :returns: response content from the API
    :rtype: dict
    """
    xml_validation = utils.validate_filetype(file_path=path_to_template_file, file_extension=".xml")
    if not xml_validation:
        msg = f"Non-existing file path or invalid extension for the path_to_template_file argument!"
        raise SystemExit(msg)
    url = settings.API_URL + f"dmp/process-template/"
    multipart_form_data = {
        'template': open(path_to_template_file, "rb")}
    r = utils.post_request_with_multipart_data(url=url, multipart_data=multipart_form_data)
    content = r.json()
    return content


def show_dmp_mapping(dmp_mapping_id):
    """
    Function that shows dmp mapping based on its identifier.

    .. seealso::
        :func:`~list_accepted_dmp_templates`

    :param dmp_mapping_id: mapping id
    :type: str
    :returns: response content from the API
    :rtype: dict
    """
    accepted_templates = list_accepted_dmp_templates()
    if dmp_mapping_id not in accepted_templates:
        msg = f"Illegal dmp_mapping_id. Has to be one of: {accepted_templates}!"
        raise SystemExit(msg)
    url = settings.API_URL + f"dmp/{dmp_mapping_id}/mapping/"
    r = utils.get_request(url=url)
    content = r.json()
    return content


@validate_authentication_token
def import_dmp(dmp_url, xml_input, json_input=None):
    """
    Function for importing DMP.

    .. note::
        xml_input filename should match json_input (except the extension)!

    :param dmp_url: DMP url from Argos
    :type: str
    :param xml_input: path to the existing DMP file in the xml format
    :type: str
    :param json_input: path to the existing DMP file in json format, optional
    :type: str
    :returns: newly created research object
    :rtype: ResearchObject
    """
    url = settings.API_URL + f"dmp/import-dmp/"
    data = {"dmp_url": dmp_url}
    xml_validation = utils.validate_filetype(file_path=xml_input, file_extension=".xml")
    if not xml_validation:
        msg = f"Non-existing file path or invalid extension for the xml_input!"
        raise SystemExit(msg)
    if json_input:
        json_validation = utils.validate_filetype(file_path=json_input, file_extension=".json")
        if not json_validation:
            msg = f"Non-existing file path or invalid extension for the json_input!"
            raise SystemExit(msg)
        multipart_data = {"file_xml": open(xml_input, "rb"),
                          "file_json": open(json_input, "rb")}
    else:
        multipart_data = {"file_xml": open(xml_input, "rb")}
    r = utils.post_request_with_multipart_data_and_regular_data(url=url, multipart_data=multipart_data, data=data)
    content = r.json()
    job_id = content.get("identifier")
    if job_id:
        job_response = is_job_success(job_id=job_id)
        job_results = job_response.get("results")
        job_warnings = job_response.get("warnings")
        if job_warnings:
            print(f"WARNING: {job_warnings}")
        try:
            ro_id = job_results.split("/")[-2]  # grab ro_id from ro url
        except AttributeError:
            msg = "Unexpected response content from the API! Couldn't parse ResearchObject id!"
            raise SystemExit(msg)
        return ros_load(identifier=ro_id)
    else:
        msg = "Incorrect job response, couldn't validate if file was uploaded or not."
        raise SystemExit(msg)


def show_relations(source=None, a_type=None, destination=None, search=None, verbose=False):
    """
    Function for displaying data regarding relations between rohub objects i.e. relation between resources.

    :param source: source object for the relation, optional
    :type: source: str
    :param a_type: type of relation, optional
    :type: a_type: str
    :param destination: destination object for the relation, optional
    :type: destination: str
    :param search: a phrase to search against
    :type: search: str
    :param verbose: if True full details will be displayed, otherwise only most important information
    :type: verbose: bool
    :returns: table containing selected information about relations
    :rtype: Panda's DataFrame
    """
    url = settings.API_URL + f"relations/"
    data = {"source": source,
            "type": a_type,
            "destination": destination,
            "search": search}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.get_request_with_params(url=url, params=data, use_token=False)
    content = r.json()
    results = content.get("results")
    while content["next"]:
        r = utils.get_request(url=content["next"])
        content = r.json()
        results.extend(content.get("results"))
    df = pd.DataFrame(results)
    if not verbose:
        if not df.empty:
            selected_columns = ['source_identifier', 'source_title', 'source_type', 'type', 'destination_identifier',
                                'destination_title', 'destination_type']
            df.drop(df.columns.difference(selected_columns), axis=1, inplace=True)
            column_sequence = ['source_identifier', 'source_title', 'source_type', 'type', 'destination_identifier',
                               'destination_title', 'destination_type']
            df = df.reindex(columns=column_sequence)
    return df


def ontologies_find(uri=None, search=None):
    """
    Function for finding and listing available ontologies.

    :param uri: ontology URI, optional
    :type: source: str
    :param search: name or description of an ontology, optional
    :type: search: str
    :returns: response content from the API
    :rtype: dict
    """
    url = settings.API_URL + f"search/ontologies/"
    data = {"uri": uri,
            "search": search}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.get_request_with_params(url=url, params=data, use_token=False)
    content = r.json()
    results = content.get("results")
    return results


@validate_authentication_token
def comments_find(created_on=None, created_by=None, modified_on=None, modified_by=None, research_object_id=None,
                  parent_comment_id=None):
    """
    Function that lists all the comments based on filters.

    :param created_on: creation date, optional.
    :type: created_on: str
    :param created_by: creator, optional
    :type: created_by: str
    :param modified_on: modification date, optional.
    :type: modified_on: str
    :param modified_by: modifier, optional.
    :type: modified_by: str
    :param research_object_id: RO identifier, optional.
    :type: research_object_id: str
    :param parent_comment_id: parent comment identifier, optional.
    :type: parent_comment_id: str
    :returns: response content from the API
    :rtype: dict
    """
    url = settings.API_URL + f"comments/"
    data = {"created_on": created_on,
            "created_by": created_by,
            "modified_on": modified_on,
            "modified_by": modified_by,
            "ro": research_object_id,
            "parent_comment": parent_comment_id}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.get_request_with_params(url=url, params=data, use_token=True)
    content = r.json()
    results = content.get("results")
    return results


@validate_authentication_token
def comments_create(body, research_object_id, parent_comment_id=None):
    """
    Function for creating a comment.

    :param body: body for the comment.
    :type: body: str
    :param research_object_id: identifier of RO that comment refers to.
    :type: research_object_id: str
    :param parent_comment_id: identifier of parent comment if there is one, optional.
    :type: parent_comment_id: str
    :returns: response content from the API
    :rtype: dict
    """
    url = settings.API_URL + f"comments/"
    data = {"text": body,
            "ro": research_object_id,
            "parent_comment": parent_comment_id}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.post_request(url=url, data=data)
    content = r.json()
    return content


def metadata_flatten(subject_shared_url):
    """
    Function for displaying pairs of predicate:object associated with a particular subject.

    :param subject_shared_url: shared_url for either ResearchObject, Resource or Folder objects
    :type: subject_shared_url: str
    :returns: table containing pairs of predicate and object associated with requested subject.
    :rtype: Panda's DataFrame
    """
    url = settings.API_URL + f"triples/"
    data = {"subject": subject_shared_url}
    data = {key: value for key, value in data.items() if value is not None}
    r = utils.get_request_with_params(url=url, params=data, use_token=True)
    content = r.json()
    results = content.get("results")
    while content["next"]:
        r = utils.get_request(url=content["next"])
        content = r.json()
        results.extend(content.get("results"))
    df = pd.DataFrame(results)
    if not df.empty:
        selected_columns = ['predicate', 'object']
        df.drop(df.columns.difference(selected_columns), axis=1, inplace=True)
        column_sequence = ['predicate', 'object']
        df = df.reindex(columns=column_sequence)
    return df


def query_sparql_endpoint(query, endpoint_url=settings.SPARQL_ENDPOINT):
    """
    Function for querying SPARQL endpoint and returning results as DataFrame.

    .. warning::
        for very big queries containing more than 100 000 rows you should consider using LIMIT and OFFSET in your query
        to avoid performance bottleneck as results are being loaded into memory all at once!

    :param endpoint_url: SPARQL endpoint, default is set to either production or dev instance of ROHUB's Virtuoso server
    :type: str
    :param query: SPARQL query
    :type: str
    :returns: table containing queried triples
    :rtype: Panda's DataFrame
    """
    headers = {"Accept": "application/sparql-results+json"}
    response = requests.get(endpoint_url, params={"query": query}, headers=headers)
    response.raise_for_status()  # raises exception if query failed

    data = response.json()

    cols = data["head"]["vars"]
    rows = []
    for binding in data["results"]["bindings"]:
        row = []
        for col in cols:
            row.append(binding[col]["value"] if col in binding else None)
        rows.append(row)

    return pd.DataFrame(rows, columns=cols)
