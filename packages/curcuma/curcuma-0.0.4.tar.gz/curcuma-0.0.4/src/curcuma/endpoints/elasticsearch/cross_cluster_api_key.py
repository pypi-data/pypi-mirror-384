# pylint: disable=W0123,W0621,W0622,W0718,W1203
"""
Elasticsearch Cross-Cluster API Key client.

This module provides the CrossClusterApiKey class for managing Elasticsearch cross-cluster API keys.
It allows creating, listing, and deleting cross-cluster API keys.

References:
  - API: https://www.elastic.co/guide/en/elasticsearch/reference/current/security-api-create-cross-cluster-api-key.html
"""

from ...endpoint import Endpoint
from ...exceptions import NotFoundException


class CrossClusterApiKey(Endpoint):
    BASE_URL = "/_security/cross_cluster/api_key"

    def create(self, body: dict):
        """
        Create a new cross-cluster API key.

        Args:
            body (dict): The API key creation request body.

        Returns:
            dict: The created API key information.
        """
        self.logger.info("Creating cross-cluster API key")
        result = self._post(CrossClusterApiKey.BASE_URL, json=body)
        return result["encoded"]

    def create_with_template(self, template_name: str, template_params: dict = None):
        """
        Create a new cross-cluster API key using a template.

        Args:
            template_name (str): The template name.
            template_params (dict, optional): Parameters for the template.
        """
        config = self._render_template("elasticsearch/cross_cluster_api_key", template_name, template_params)
        return self.create(config)

    def get(self, id: str):
        """
        Retrieve a cross-cluster API key by its ID.

        Args:
            id (str): The API key ID.

        Returns:
            dict: The API key information.
        """
        self.logger.info(f"Getting cross-cluster API key '{id}'")
        return self._get(f"{CrossClusterApiKey.BASE_URL}/{id}")

    def list(self, filter: str = None):
        """
        Print all cross-cluster API keys, optionally filtered by name.

        Args:
            filter (str, optional): Regex pattern to filter API key names.
        """
        import re

        pattern = re.compile(filter) if filter else None
        r = self._get(CrossClusterApiKey.BASE_URL)
        for api_key in r.get("api_keys", []):
            name = api_key.get("name")
            if pattern and not pattern.search(name):
                continue
            print(f"API Key: {name}")
            print(f"  ID: {api_key.get('id')}")
            print(f"  Creation: {api_key.get('creation')}")
            print(f"  Expiration: {api_key.get('expiration')}")
            print(f"  Metadata: {api_key.get('metadata')}")

    # def delete(self, id: str):
    #     """
    #     Delete a cross-cluster API key by its ID.

    #     Args:
    #         id (str): The API key ID.
    #     """
    #     self.logger.info(f"Deleting cross-cluster API key '{id}'")
    #     try:
    #         self._delete(CrossClusterApiKey.BASE_URL, json={"ids": ["{id}"]})
    #     except NotFoundException:
    #         pass
