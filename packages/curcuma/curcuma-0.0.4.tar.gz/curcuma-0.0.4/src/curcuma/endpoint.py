# pylint: disable=W0123,W0621,W0622,W0718,W1203
"""
Base Endpoint class for Curcuma API clients.

This module provides the Endpoint class, which implements generic HTTP methods (GET, POST, PUT, DELETE)
and utility functions for interacting with RESTful APIs using httpx. It also provides template rendering
and response handling, as well as deep diffing for configuration changes.

Classes:
    - Endpoint: Base class for API endpoint clients, providing HTTP and template utilities.

Exceptions:
    - CurcumaException: Raised for general API errors.
    - ConflictException: Raised for resource conflicts.
    - NotFoundException: Raised when a resource is not found.
    - PermissionException: Raised for permission errors.
    - TemplateParameterException: Raised for missing template parameters.
"""

import json
import os
import sys

import httpx
from deepdiff import DeepDiff
from jinja2 import Environment, FileSystemLoader, meta, TemplateNotFound

from .exceptions import (
    CurcumaException,
    ConflictException,
    NotFoundException,
    PermissionException,
    TemplateParameterException,
)

from .log import get_logger

logger = get_logger(__name__)


class Endpoint:
    """
    Base class for Curcuma API endpoint clients.

    Provides generic HTTP methods (GET, POST, PUT, DELETE), template rendering, response handling,
    and configuration diffing utilities for derived API clients.
    """

    simulate = False

    def __init__(self, client: httpx.Client, name: str = None):
        """
        Initialize the Endpoint with an HTTP client.

        Args:
            client (httpx.Client): The HTTP client to use for requests.
        """
        self._clt = client
        self.logger = get_logger(name if name else __name__)

    def _get(self, url: str):
        """
        Perform a GET request.

        Args:
            url (str): The URL to request.

        Returns:
            Any: The parsed response.
        """
        self.logger.debug(f"connecting to {url} via GET")
        try:
            response = self._clt.get(url)
            return self._response_handler(response)
        except httpx.ConnectError as e:
            self.logger.error(e)
            sys.exit(1)

    def _patch(self, url: str, json: dict = None):
        """
        Perform a PATCH request.

        Args:
            url (str): The URL to request.
            json (dict, optional): The JSON body to send.

        Returns:
            Any: The parsed response.
        """
        if self.simulate:
            return {"simulated": True}
        self.logger.debug(f"connecting to {url} via PATCH")
        try:
            response = self._clt.patch(url, json=json)
            return self._response_handler(response)
        except httpx.ConnectError as e:
            self.logger.error(e)
            sys.exit(1)

    def _post(self, url: str, json: dict = None):
        """
        Perform a POST request.

        Args:
            url (str): The URL to request.
            json (dict, optional): The JSON body to send.

        Returns:
            Any: The parsed response.
        """
        if self.simulate:
            return {"simulated": True}
        self.logger.debug(f"connecting to {url} via POST")
        try:
            response = self._clt.post(url, json=json)
            return self._response_handler(response)
        except httpx.ConnectError as e:
            self.logger.error(e)
            sys.exit(1)

    def _put(self, url: str, json: dict = None):
        """
        Perform a PUT request.

        Args:
            url (str): The URL to request.
            json (dict, optional): The JSON body to send.

        Returns:
            Any: The parsed response.
        """
        if self.simulate:
            return
        self.logger.debug(f"connecting to {url} via PUT")
        try:
            response = self._clt.put(url, json=json)
            return self._response_handler(response)
        except httpx.ConnectError as e:
            self.logger.error(e)
            sys.exit(1)

    def _delete(self, url: str, json: dict = None):
        """
        Perform a DELETE request.

        Args:
            url (str): The URL to request.
            json (dict, optional): The JSON body to send.

        Returns:
            Any: The parsed response.
        """
        if self.simulate:
            return
        self.logger.debug(f"connecting to {url} via DELETE")
        try:
            if not json:
                response = self._clt.delete(url, json=json)
            else:
                import requests

                # self.
                response = requests.delete(url, json=json)
            return self._response_handler(response)
        except httpx.ConnectError as e:
            self.logger.error(e)
            sys.exit(1)

    @staticmethod
    def _fpretty(key: str):
        """
        Format a diff key for pretty printing.

        Args:
            key (str): The diff key.

        Returns:
            str: The formatted key.
        """
        return key[5:-1].replace("][", ".").replace("'", "")

    def _deepdiff(self, old: dict, new: dict, show_untouched: bool = False, prefix: str = "") -> DeepDiff:
        """
        Compute and log the deep differences between two dictionaries.

        Args:
            old (dict): The original dictionary.
            new (dict): The new dictionary.
            show_untouched (bool, optional): Whether to show removed items. Defaults to False.
            prefix (str, optional): Prefix for nested keys.

        Returns:
            dict: Added or changed items.
        """
        if len(prefix) == 0:
            self.logger.debug("determining the differences")
        diff = DeepDiff(old, new, ignore_order=True, verbose_level=2, threshold_to_diff_deeper=0)
        self.logger.debug(diff.get_stats())

        changes = {}
        added = diff.get("iterable_item_added")
        if added:
            # self.logger.info("new:")
            changes["new"] = []
            for a in added:
                changes["new"].append(f" - {Endpoint._fpretty(a)} => {added[a]}")
                # self.logger.info(f" - {Endpoint._fpretty(a)} => {added[a]}")

        changed = diff.get("values_changed")
        if changed:
            if len(prefix) == 0:
                # self.logger.info("changes:")
                changes["changes"] = []
            for c in changed:
                if isinstance(changed[c]["old_value"], dict) or isinstance(changed[c]["new_value"], dict):
                    self._deepdiff(
                        changed[c]["old_value"],
                        changed[c]["new_value"],
                        prefix=f"{prefix}{Endpoint._fpretty(c)}.",
                    )
                else:
                    changes["changes"].append(
                        f" - {prefix}{Endpoint._fpretty(c)} changes from '{changed[c]['old_value']}' to '{changed[c]['new_value']}'"
                    )
                    # self.logger.info(
                    #     f" - {prefix}{Endpoint._fpretty(c)} changes from '{changed[c]['old_value']}' to '{changed[c]['new_value']}'"
                    # )

        if show_untouched:
            removed = diff.get("dictionary_item_removed")
            if removed:
                self.logger.debug("untouched:")
                for r in removed:
                    val = eval(r.replace("root", "old"))
                    if type(val) is not bool and len(val) == 0:
                        continue
                    self.logger.debug(f" - {Endpoint._fpretty(r)} => {removed[r]}")

        return changes

    def _log_diff(self, diff: dict):
        for type in diff:
            self.logger.warning("%s:", type)
            for item in diff[type]:
                self.logger.warning(item)

    def _render_template(self, path, name, params, check: bool = True):
        """
        Render a Jinja2 template and return the parsed JSON.

        Args:
            path (str): Template directory path.
            name (str): Template name (without extension).
            params (dict): Parameters for rendering.
            check (bool, optional): Whether to check for missing parameters. Defaults to True.

        Returns:
            dict: The rendered and parsed template.

        Raises:
            TemplateParameterException: If required template parameters are missing.
        """
        try:
            if params is None:
                params = {}
            package_root = os.path.dirname(__file__)
            template_file = name + ".json.j2"
            env = Environment(loader=FileSystemLoader(f"{package_root}/templates/{path}"))
            if check:
                template_source = env.loader.get_source(env, template_file)[0]
                parsed_content = env.parse(template_source)
                variables = meta.find_undeclared_variables(parsed_content)
                diff = list(variables.difference(set(params)))
                if len(diff) > 0:
                    self.logger.error(f"Missing parameters: {diff}")
                    raise TemplateParameterException(f"Missing template parameters: {diff}")

            template = env.get_template(template_file)
            config = template.render(params)
            return json.loads(config)
        except TemplateNotFound as e:
            self.logger.error(e.message)
            sys.exit(1)

    def _response_handler(self, r: httpx.Response):
        """
        Handle and parse an HTTP response.

        Args:
            r (httpx.Response): The HTTP response.

        Returns:
            Any: The parsed response content.

        Raises:
            CurcumaException: For various HTTP error codes.
        """
        self._status_handler(r)
        try:
            if r.status_code == 204:
                return None
            elif r.text.startswith("{") or r.text.startswith("["):
                return r.json()
            else:
                return r.text
        except Exception as e:
            self.logger.error(e)
            self.logger.debug(r.text)

    def _status_handler(self, r: httpx.Response):
        """
        Handle HTTP status codes and raise exceptions as needed.

        Args:
            r (httpx.Response): The HTTP response.

        Raises:
            NotFoundException: For 404 status code.
            PermissionException: For 403 status code.
            ConflictException: For 409 or duplicate/conflict 400 status code.
            CurcumaException: For other error status codes.
        """
        self.logger.debug(f"status code: {r.status_code}")
        self.logger.debug(f"response body: {r.text}")
        if r.status_code <= 210:
            self.logger.debug("done")
        elif r.status_code == 302:
            self.logger.info("relocated")
            raise NotFoundException(f"Status {r.status_code} - {r.headers['Location']}")
        elif r.status_code == 403:
            self.logger.error("permission denied")
            raise PermissionException(f"Status {r.status_code} - {r.text}")
        elif r.status_code == 404:
            self.logger.debug("not found")
            raise NotFoundException(
                f"Status {r.status_code}({r.json().get('error')}) - {r.json().get('message', r.text)}"
            )
        elif (
            r.status_code == 409
            or r.status_code == 400
            and (
                r.json().get("message", r.text).startswith("Duplicate")
                or r.json().get("message", r.text).endswith("conflict")
            )
        ):
            self.logger.error(f"Status {r.status_code}({r.json().get('error')}) - {r.json().get('message', r.text)}")
            raise ConflictException(r.text)
        elif r.status_code >= 400:
            self.logger.error(f"Status {r.status_code} - {r.json().get('message', r.text)}")
            raise CurcumaException(f"Status {r.status_code} - {r.json().get('message', r.text)}")
