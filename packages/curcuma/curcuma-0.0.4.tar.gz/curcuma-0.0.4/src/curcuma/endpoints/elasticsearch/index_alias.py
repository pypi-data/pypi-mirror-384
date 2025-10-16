# https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-indices-put-alias

import re

from loguru import logger

from ...endpoint import Endpoint
from ...exceptions import NotFoundException


class IndexAlias(Endpoint):
    """
    Client for managing Elasticsearch index aliases.

    Provides methods to retrieve, list, create, and delete index aliases.
    """

    BASE_URL = "/_aliases/"

    def get(self):
        """
        Retrieve all index aliases.

        Returns:
            dict: All index aliases.
        """
        return self._get(IndexAlias.BASE_URL)

    def list(self, filter: str = None):
        """
        Print all index aliases, optionally filtered by index name.

        Args:
            filter (str, optional): Regex pattern to filter index names.
        """
        pattern = re.compile(filter) if filter else None
        r = self.get()
        for name in sorted(r.keys()):
            try:
                if pattern and not pattern.search(name):
                    continue
                print(f"Index: {name}")
                for alias in r[name]["aliases"]:
                    print(f"  Alias: {alias}")
                    for key, value in r[name]["aliases"][alias].items():
                        print(f"    {key}: {value}")
            except KeyError:
                print(f"Index: {name}, Config: {r[name]}")

    def set(self, body: dict):
        """
        Create or update an index alias.

        Args:
            body (dict): The alias configuration body.
        """
        self.logger.info(f"Setting index alias '{body.get('actions')[0].get('add').get('alias')}'")
        self._post(IndexAlias.BASE_URL, json=body)

    def set_with_template(self, template_name: str, template_params: dict = None):
        """
        Create or update an index alias using a template.

        Args:
            template_name (str): The template name.
            template_params (dict, optional): Parameters for the template.
        """
        self.logger.debug(f'Using index_alias template "{template_name}" with params "{template_params}"')
        config = self._render_template("elasticsearch/index_alias", template_name, template_params)
        self.set(config)

    def delete(self, index: str, alias: str):
        """
        Delete an index alias from a specific index.

        Args:
            index (str): The index name.
            alias (str): The alias name.
        """
        self.logger.info(f"Deleting index alias '{alias}' from index '{index}'")
        try:
            self._delete(index + IndexAlias.BASE_URL + alias)
        except NotFoundException:
            pass
