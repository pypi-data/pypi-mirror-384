# Internal imports
from rohub import utils
from rohub import settings
from rohub import rohub


class Folder(object):
    """
    Class Representation of Rohub's folder.

    .. note::

        | **editable attributes:**
        | - name
        | - ro_id
        | - parent_folder
        | - description

        | **read-only attributes:**
        | - identifier
        | - path
        | - size
        | - order
        | - created
        | - creator
        | - modificator
        | - modified
        | - created_on
        | - created_by
        | - modified
        | - authors_credits
        | - contributors_credits
        | - shared_link
        | - count
        | - has_annotations
        | - api_link
    """

    def __init__(self, ro_id=None, name=None, parent_folder=None, description=None, identifier=None, post_request=True):
        """
        Constructor for the Folder object.

        :param ro_id: research object's identifier, optional
        :type ro_id: str
        :param name: folder's name, optional
        :type name: str
        :param parent_folder: parent folder id, optional
        :type parent_folder: str
        :param description: resource's description
        :type description: str
        :param identifier: resource's identifier, optional, used when object already exists and has to be loaded
        :type identifier: str
        :param post_request: if True, the object will be created, otherwise loaded - default is True
        :type post_request: bool
        """
        if self._is_valid():
            # Main.
            self.folder_response_content = {}

            if post_request:
                # Required attributes
                self.ro_id = ro_id  # REGULAR
                self.name = name  # REGULAR
                # Optional attributes
                self.parent_folder = parent_folder  # TYPE VALIDATION
                self.description = description  # TYPE VALIDATION
                # Crating new Folder.
                self._post_folder()
            else:
                self.__identifier = identifier
                # Loading existing Research Object.
                self._load_folder()

            # Updating required attributes with values from the response.
            self.name = self.folder_response_content.get("name")
            self.ro_id = self.folder_response_content.get("ro")

            # Updating optional attributes with values from the response.
            self.description = self.folder_response_content.get("description")
            self.parent_folder = utils.map_folder_id_to_path(self.folder_response_content.get("parent_folder"))

            # ReadOnly attributes; will be updated after request post.
            self.__identifier = self.folder_response_content.get("identifier")
            self.__path = self.folder_response_content.get("path")
            self.__order = self.folder_response_content.get("order")
            self.__created = self.folder_response_content.get("created")
            self.__creator = self.folder_response_content.get("creator")
            self.__modificator = self.folder_response_content.get("modificator")
            self.__modified = self.folder_response_content.get("modified")
            self.__created_on = self.folder_response_content.get("created_on")
            self.__created_by = self.folder_response_content.get("created_by")
            self.__modified_on = self.folder_response_content.get("modified_on")
            self.__modified_by = self.folder_response_content.get("modified_by")
            self.__authors_credits = self.folder_response_content.get("authors_credits")
            self.__contributors_credits = self.folder_response_content.get("contributors_credits")
            self.__has_annotations = self.folder_response_content.get("has_annotations")
            self.__count = self.folder_response_content.get("count")
            self.__api_link = self.folder_response_content.get("api_link")
            self.__shared_link = self.folder_response_content.get("shared_link")

            # Other Attributes.
            self.update_response_content = None

            if post_request:
                print(f"Folder was successfully created with id = {self.identifier}")
            else:
                print(f"Folder was successfully loaded with id = {self.identifier}")
        else:
            print('Token is no longer valid! Use login function to generate a new one!')

    def __str__(self):
        return f"Folder with ID: {self.identifier}"

    def __repr__(self):
        return f"Folder(identifier={self.identifier}, post_request=False)"

    ###############################################################################
    #              Properties.                                                    #
    ###############################################################################
    @property
    def identifier(self):
        return self.__identifier

    @identifier.setter
    def identifier(self, value):
        raise AttributeError('This is a read-only attribute!')

    @property
    def path(self):
        return self.__path

    @path.setter
    def path(self, value):
        raise AttributeError('This is a read-only attribute!')

    @property
    def order(self):
        return self.__order

    @order.setter
    def order(self, value):
        raise AttributeError('This is a read-only attribute!')

    @property
    def created(self):
        return self.__created

    @created.setter
    def created(self, value):
        raise AttributeError('This is a read-only attribute!')

    @property
    def creator(self):
        return self.__creator

    @creator.setter
    def creator(self, value):
        raise AttributeError('This is a read-only attribute!')

    @property
    def modificator(self):
        return self.__modificator

    @modificator.setter
    def modificator(self, value):
        raise AttributeError('This is a read-only attribute!')

    @property
    def modified(self):
        return self.__modified

    @modified.setter
    def modified(self, value):
        raise AttributeError('This is a read-only attribute!')

    @property
    def created_on(self):
        return self.__created_on

    @created_on.setter
    def created_on(self, value):
        raise AttributeError('This is a read-only attribute!')

    @property
    def created_by(self):
        return self.__created_by

    @created_by.setter
    def created_by(self, value):
        raise AttributeError('This is a read-only attribute!')

    @property
    def modified_on(self):
        return self.__modified_on

    @modified_on.setter
    def modified_on(self, value):
        raise AttributeError('This is a read-only attribute!')

    @property
    def modified_by(self):
        return self.__modified_by

    @modified_by.setter
    def modified_by(self, value):
        raise AttributeError('This is a read-only attribute!')

    @property
    def authors_credits(self):
        return self.__authors_credits

    @authors_credits.setter
    def authors_credits(self, value):
        raise AttributeError('This is a read-only attribute!')

    @property
    def contributors_credits(self):
        return self.__contributors_credits

    @contributors_credits.setter
    def contributors_credits(self, value):
        raise AttributeError('This is a read-only attribute!')

    @property
    def has_annotations(self):
        return self.__has_annotations

    @has_annotations.setter
    def has_annotations(self, value):
        raise AttributeError('This is a read-only attribute!')

    @property
    def count(self):
        return self.__count

    @count.setter
    def count(self, value):
        raise AttributeError('This is a read-only attribute!')

    @property
    def api_link(self):
        return self.__api_link

    @api_link.setter
    def api_link(self, value):
        raise AttributeError('This is a read-only attribute!')

    @property
    def shared_link(self):
        return self.__shared_link

    @shared_link.setter
    def shared_link(self, value):
        raise AttributeError('This is a read-only attribute!')

    ###############################################################################
    #              Main Methods.                                                  #
    ###############################################################################

    @staticmethod
    def _is_valid():
        """
        Semi-Private function that checks if current token is still valid, and if not it attempts
        to refresh it.
        :return: boolean -> True if valid, False otherwise.
        """
        if utils.is_valid(token_type="access"):
            valid_token = True
        else:
            valid_token = utils.refresh_access_token()
        return valid_token

    def _post_folder(self):
        """
        Semi-private function that creates post request for a resource given
        required and optional parameters.
        """
        data = {"name": self.name,
                "description": self.description,
                "parent_folder": self.parent_folder}
        data = {key: value for key, value in data.items() if value is not None}
        url = settings.API_URL + f"ros/{self.ro_id}/folders/"
        if self._is_valid():
            r = utils.post_request(url=url, data=data)
            self.folder_response_content = r.json()
        else:
            msg = "Your current access token is either missing or expired, please log into" \
                  " rohub again"
            raise SystemExit(msg)

    def _load_folder(self):
        """
        Semi-private function that creates get request for existing Resource.
        """
        if self._is_valid():
            self.folder_response_content = rohub.folder_search_using_id(folder_identifier=self.identifier)
        else:
            msg = "Your current access token is either missing or expired, please log into" \
                  " rohub again"
            raise SystemExit(msg)

    def show_metadata(self):
        """
        Function that shows selected (most relevant) information regarding folder.

        :returns: folder's most relevant metadata
        :rtype: dict
        """
        basic_metadata = {
            "identifier": self.identifier,
            "description": self.description,
            "name": self.name,
            "path": self.path,
            "ro": self.ro_id,
            "creator": self.creator,
            "created_on": self.created_on,
            "modified_on": self.modified_on,
        }
        return basic_metadata

    def show_full_metadata(self):
        """
        Function that shows all metadata associated with the folder.

        :returns: response content from the API
        :rtype: dict
        """
        return self.folder_response_content

    def delete(self):
        """
        Function that deletes folder.

        .. warning::
            The folder will be deleted from the service and will no longer appear in the API.
            This doesn't mean that object created in your local scope will be removed!

        :returns: None
        :rtype: None
        """
        rohub.folder_delete(folder_identifier=self.identifier)

    def update(self):
        """
        Function for updating folder object in the service.

        .. note::
            After executing update_metadata the resource will be updated in the service with accordance
            to the changes that were made to the python object in your local scope.

        :returns: response content from the API
        :rtype: dict
        """
        self.update_response_content = rohub.folder_update(identifier=self.identifier, name=self.name,
                                                           ro_identifier=self.ro_id, description=self.description,
                                                           parent_folder=self.parent_folder)
        return self.update_response_content
