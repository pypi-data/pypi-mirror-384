# pylint: disable=W1203,W0621,W0123,W0718,W0622,W0212
"""
Kibana Data Views API client.

This module provides the DataView class for managing Kibana Data Views via the Data Views API.
It allows creating, updating, deleting, and querying data views within a specified Kibana space.

References:
    - Kibana Data Views API documentation: https://www.elastic.co/guide/en/kibana/8.12/data-views-api.html
"""

import json
import sys

from ...endpoint import Endpoint
from ...exceptions import NotFoundException


class DataView(Endpoint):
    """
    A client for managing Kibana Data Views via the Data Views API.

    Provides methods to create, update, delete, and query data views in a given Kibana space.
    """

    BASE_URL = "/s/{space_id}/api/data_views"

    def default(self, space_id: str, id: str):
        """
        Set the specified data view as the default for the given space.

        Args:
            space_id (str): The Kibana space ID.
            id (str): The data view ID to set as default.
        """
        self.logger.info(f"Setting data view '{id}' in space '{space_id}' as default")
        self._post(f"{DataView.BASE_URL}/default", json={"data_view_id": id})

    def get(self, space_id: str, id: str):
        """
        Retrieve a data view by its ID.

        Args:
            space_id (str): The Kibana space ID.
            id (str): The data view ID.

        Returns:
            dict: The data view object.
        """
        self.logger.info(f"Reading data view '{id}'")
        return self._get(f"{DataView.BASE_URL}/data_view/{id}".format(space_id=space_id))

    def show(self, space_id: str, id: str):
        """
        Print the data view as formatted JSON.

        Args:
            space_id (str): The Kibana space ID.
            id (str): The data view ID.
        """
        role = self.get(space_id, id)
        print(json.dumps(role, indent=2))

    def get_all(self, space_id: str):
        """
        Retrieve all data views in the specified space.

        Args:
            space_id (str): The Kibana space ID.

        Returns:
            list: List of data view objects.
        """
        self.logger.info("Reading data views")
        return self._get(f"{DataView.BASE_URL}".format(space_id=space_id))

    def get_id(self, space_id: str, name: str):
        """
        Get the ID of a data view by its name.

        Args:
            space_id (str): The Kibana space ID.
            name (str): The name of the data view.

        Returns:
            str: The data view ID, or None if not found.
        """
        for dataview in self.get_all(space_id):
            if dataview.get("name") == name:
                return dataview.get("id")

    def exits(self, space_id: str, name: str = None, id: str = None):
        """
        Check if a data view exists by name or ID.

        Args:
            space_id (str): The Kibana space ID.
            name (str, optional): The name of the data view.
            id (str, optional): The ID of the data view.

        Returns:
            bool: True if the data view exists, False otherwise.

        Raises:
            AttributeError: If both name and id are provided.
        """
        if name is not None and id is not None:
            raise AttributeError(f"{self.__class__}.{sys._getframe().f_code.co_name}() supports name or id, not both")
        if id is not None:
            try:
                self.get(space_id, id)
                return True
            except NotFoundException:
                return False
        else:
            for dv in self.get_all(space_id).get("data_view"):
                if dv.get("name") == name:
                    return True
            return False

    def list(self, space_id: str):
        """
        Print all data views in the specified space.

        Args:
            space_id (str): The Kibana space ID.
        """
        for data_view in self.get_all(space_id):
            print(f"DataView: {data_view}")

    def create(self, space_id: str, config: dict):
        """
        Create a new data view with the given configuration.

        Args:
            space_id (str): The Kibana space ID.
            config (dict): The data view configuration.
        """
        data_view = config.get("data_view")
        self.logger.warning(f"Creating data view '{data_view.get('id')}'")
        self._post(f"{DataView.BASE_URL}/data_view".format(space_id=space_id), json=config)

    def update(self, space_id: str, config: dict):
        """
        Update an existing data view with the given configuration.

        Args:
            space_id (str): The Kibana space ID.
            config (dict): The data view configuration (must include 'id').
        """
        id = config["data_view"]["id"]
        try:
            cur_conf = self._get(f"{DataView.BASE_URL}/data_view/{id}".format(space_id=space_id))
            diff = self._deepdiff(cur_conf, config)
            if diff:
                self.logger.warning(f"Updating data view '{id}'")
                self._log_diff(diff)
            else:
                self.logger.info(f"Data view '{id}' is up-to-date")
            del config["data_view"]["id"]
            self._post(f"{DataView.BASE_URL}/data_view/{id}".format(space_id=space_id), json=config)
        except NotFoundException:
            self.create(space_id, config)

    def create_with_template(self, space_id: str, template_name: str, template_params: dict = None):
        """
        Create a data view using a template.

        Args:
            space_id (str): The Kibana space ID.
            template_name (str): The template name.
            template_params (dict, optional): Parameters for the template.
        """
        config = self._render_template("kibana/data_view", template_name, template_params)
        self.create(space_id, config)

    def update_with_template(self, space_id: str, template_name: str, template_params: dict = None):
        """
        Update a data view using a template.

        Args:
            space_id (str): The Kibana space ID.
            template_name (str): The template name.
            template_params (dict, optional): Parameters for the template.
        """
        config = self._render_template("kibana/data_view", template_name, template_params)
        self.update(space_id, config)

    def set_with_template(self, space_id: str, template_name: str, template_params: dict = None):
        """
        Create or update a data view using a template, depending on existence.

        Args:
            space_id (str): The Kibana space ID.
            template_name (str): The template name.
            template_params (dict, optional): Parameters for the template.
        """
        if not self.exits(space_id, id=template_params.get("id")):
            self.create_with_template(space_id, template_name, template_params)
        else:
            self.update_with_template(space_id, template_name, template_params)

    def delete(self, space_id: str, id: str):
        """
        Delete a data view by its ID.

        Args:
            space_id (str): The Kibana space ID.
            id (str): The data view ID.
        """
        self.logger.info(f"Deleting data view '{id}' from space '{space_id}'")
        try:
            self._delete(f"{DataView.BASE_URL}/data_view/{id}".format(space_id=space_id))
        except NotFoundException:
            pass

    def delete_by_name(self, space_id: str, name: str):
        """
        Delete a data view by its name.

        Args:
            space_id (str): The Kibana space ID.
            name (str): The name of the data view.
        """
        self.delete(space_id, self.get_id(space_id, name))
