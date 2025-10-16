# pylint: disable=W1203,W0621,W0123,W0718,W0622
# https://www.elastic.co/docs/api/doc/kibana/group/endpoint-roles

import json
import re

from ...endpoint import Endpoint
from ...exceptions import NotFoundException


class Role(Endpoint):
    """
    Client for managing Kibana roles.

    Provides methods to retrieve, list, compare, create, update, and delete roles in Kibana.
    """

    BASE_URL = "/api/security/role"

    def get(self, name: str) -> dict:
        """
        Retrieve a role by its name.

        Args:
            name (str): The name of the role.

        Returns:
            dict: The role object.
        """
        self.logger.info(f'Reading role "{name}"')
        return self._get(f"{Role.BASE_URL}/{name}")

    def show(self, name: str):
        """
        Print the role as formatted JSON.

        Args:
            name (str): The name of the role.
        """
        role = self.get(name)
        print(json.dumps(role, indent=2))

    def get_all(self):
        """
        Retrieve all roles.

        Returns:
            list: List of all roles.
        """
        self.logger.info("Reading all roles")
        return self._get(Role.BASE_URL)

    def list(self, reserved: bool = False, filter: str = None):
        """
        Print a list of roles, optionally filtering reserved roles and by name.

        Args:
            reserved (bool, optional): Whether to include reserved roles. Defaults to False.
            filter (str, optional): Regex pattern to filter role names.
        """
        pattern = re.compile(filter) if filter else None
        r = self.get_all()
        for role in r:
            if not reserved and "_reserved" in role.get("metadata").keys():
                continue
            if pattern and not pattern.search(role["name"]):
                continue
            print(f"Role: {role['name']} \tDescription: {role['description']}")

    def compare(self, name: str, config: dict):
        """
        Compare the current role configuration with a provided configuration.

        Args:
            name (str): The name of the role.
            config (dict): The configuration to compare.
        """
        cur_conf = self.get(name)
        self.logger.info(f'Comparing role "{name}"')
        self.logger.debug(f'with config "{config}"')
        self._deepdiff(cur_conf, config)

    def set(self, name: str, config: dict):
        """
        Create or update a role with the given configuration.

        Args:
            name (str): The name of the role.
            config (dict): The role configuration.
        """
        try:
            cur_conf = self.get(name)
            self.logger.warning(f'Updating role "{name}"')
            self.logger.debug(f'with config "{config}"')
            if not self._deepdiff(cur_conf, config):
                self.logger.debug("no need for an update")
                return
        except NotFoundException:
            self.logger.warning(f'Creating role "{name}"')
            self.logger.debug(f'with config "{config}"')
        self._put(f"{Role.BASE_URL}/{name}", json=config)

    def set_with_template(self, name: str, template_name: str, template_params: dict = None):
        """
        Create or update a role using a template.

        Args:
            name (str): The name of the role.
            template_name (str): The template name.
            template_params (dict, optional): Parameters for the template.
        """
        self.logger.debug(f'Using template "{template_name}" and params "{template_params}" for role')
        config = self._render_template("kibana/role", template_name, template_params)
        self.set(name, config)

    def delete(self, name: str):
        """
        Delete a role by its name.

        Args:
            name (str): The name of the role.
        """
        self.logger.info(f'Deleting role "{name}"')
        try:
            self._delete(f"{Role.BASE_URL}/{name}")
        except NotFoundException:
            pass
