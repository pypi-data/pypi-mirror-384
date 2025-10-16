"""
Elasticsearch Data Streams API client.

This module provides the DataStream class for managing Elasticsearch Data Streams.
It allows listing, creating, and deleting data streams.

References:
    - API documentation: https://www.elastic.co/guide/en/elasticsearch/reference/current/data-streams.html
"""

import re

from ...endpoint import Endpoint
from ...exceptions import NotFoundException


class DataStream(Endpoint):
    BASE_URL = "/_data_stream/"

    def get(self):
        """
        Retrieve all data streams.

        Returns:
            dict: All data streams.
        """
        return self._get(DataStream.BASE_URL)

    def list(self, filter: str = None):
        """
        Print all data streams, optionally filtered by name.

        Args:
            filter (str, optional): Regex pattern to filter data stream names.
        """

        pattern = re.compile(filter) if filter else None
        r = self.get()
        for ds in r.get("data_streams", []):
            name = ds.get("name")
            if pattern and not pattern.search(name):
                continue
            print(f"DataStream: {name}")
            print(f"  Indices: {[i['index_name'] for i in ds.get('indices', [])]}")
            print(f"  Generation: {ds.get('generation')}")
            print(f"  Status: {ds.get('status')}")
            print(f"  Template: {ds.get('template')}")
            print(f"  Hidden: {ds.get('hidden')}")
            print(f"  System: {ds.get('system')}")

    def create(self, name: str):
        """
        Create a new data stream.

        Args:
            name (str): The name of the data stream.
        """
        self.logger.info("Creating data stream '%s'", name)
        self._put(DataStream.BASE_URL + name)

    def delete(self, name: str):
        """
        Delete a data stream.

        Args:
            name (str): The name of the data stream.
        """
        self.logger.info("Deleting data stream '%s'", name)
        try:
            self._delete(DataStream.BASE_URL + name)
        except NotFoundException:
            pass
