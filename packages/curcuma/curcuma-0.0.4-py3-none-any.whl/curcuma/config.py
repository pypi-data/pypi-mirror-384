# pylint: disable=W1203,W0621,W0123,W0718
"""
Configuration management for Curcuma.

This module provides the Config class for loading, parsing, and rendering configuration files
in JSON or YAML format, including support for credential resolution via Azure Key Vault.
It also provides the AzureKeyvault class for retrieving secrets from Azure Key Vault.

Classes:
    - Config: Handles configuration loading, template rendering, and credential resolution.
    - AzureKeyvault: Retrieves secrets from Azure Key Vault.

Exceptions:
    - CurcumaException: Raised for general configuration errors.
    - TemplateParameterException: Raised for missing template parameters.
"""

import json
import os
import sys

import yaml

# from loguru import logger
from jinja2 import Environment, FileSystemLoader, meta

from .exceptions import CurcumaException, TemplateParameterException
from .log import get_logger

logger = get_logger(__name__)


class Config:
    """
    Configuration loader and manager for Curcuma.

    Loads configuration files (JSON or YAML), renders Jinja2 templates, and resolves credentials
    using supported credential stores (currently Azure Key Vault).

    Args:
        name (str): The configuration file name.
        params (dict, optional): Parameters for template rendering.

    Attributes:
        deployment (dict): The loaded deployment configuration.
        cred_store (AzureKeyvault): The credential store instance, if configured.
    """

    def __init__(self, name: str, params: dict = {}):
        """
        Initialize the Config object by loading and parsing the configuration file.

        Args:
            name (str): The configuration file name.
            params (dict, optional): Parameters for template rendering.

        Raises:
            CurcumaException: If the file format is unsupported or other errors occur.
        """
        try:
            config = Config.render_template(os.path.expanduser("~/.curcuma/configs"), name, params)
            if name.endswith(".json"):
                config = json.loads(config)
            elif name.endswith(".yml") or name.endswith(".yaml"):
                config = yaml.safe_load(config)
            else:
                raise CurcumaException(f"unsupported file format: {name.split('.')[:-1]}")
            if "credential-store" in config:
                self.init_credential_store(config["credential-store"])
                self.resolve_creds(config.get("deployment", {}))
            self.config = config
            self.deployment = config.get("deployment", {})

        except CurcumaException as e:
            print(e)
            sys.exit(1)

    def get_deployment(self):
        """
        Get the deployment configuration.

        Returns:
            dict: The deployment configuration.
        """
        return self.config.get("deployment", {})

    def get_ech(self):
        """
        Get the deployment configuration.

        Returns:
            dict: The elastic-cloud-hosting configuration.
        """
        return self.config.get("elastic-cloud-hosting", {})

    def resolve_creds(self, branch: dict):
        """
        Recursively resolve credentials in the configuration branch.

        Args:
            branch (dict): The configuration branch to resolve credentials in.
        """
        for k, v in branch.items():
            if isinstance(v, str) and v.startswith("{cred}:"):
                try:
                    branch[k] = self.cred_store.get_secret(v[7:])
                except Exception as e:
                    if "SecretNotFound" in str(e):
                        logger.error(f"Secret '{v[7:]}' not found in credential store")
                    else:
                        logger.error(f"Reading secret '{v[7:]}' failed: {e}")
                    sys.exit(1)
            elif isinstance(v, dict):
                self.resolve_creds(branch[k])

    def init_credential_store(self, conf: dict):
        """
        Initialize the credential store from the configuration.

        Args:
            conf (dict): The credential store configuration.

        Raises:
            CurcumaException: If the file format is unsupported or no supported store is found.
        """
        if "file" in conf:
            file_path = os.path.expanduser(f"~/.curcuma/configs/{conf["file"]}")
            if conf["file"].endswith("json"):
                cs = json.load(file_path)
            elif conf["file"].endswith("yml") or conf.endswith("yaml"):
                with open(file_path, encoding="utf-8") as file:
                    yml = yaml.safe_load(file)
                    cs = yml.get("credential-store", {})
            else:
                raise CurcumaException(f"unsupported file format: {file_path.split('.')[:-1]}")
        else:
            cs = conf
        if "azure-keyvault" in cs:
            kv = cs["azure-keyvault"]
            self.cred_store = AzureKeyvault(
                kv["keyvault-name"], kv.get("tenant-id"), kv.get("client-id"), kv.get("client-secret")
            )
        else:
            logger.error("no config for one of the supported credential-stores found")
            sys.exit(1)

    @staticmethod
    def render_template(path, file, params, check: bool = True):
        """
        Render a Jinja2 template with the given parameters.

        Args:
            path (str): The path to the template directory.
            file (str): The template file name.
            params (dict): Parameters for rendering.
            check (bool, optional): Whether to check for missing parameters. Defaults to True.

        Returns:
            str: The rendered template as a string.

        Raises:
            TemplateParameterException: If required template parameters are missing.
        """
        try:
            env = Environment(loader=FileSystemLoader(path))
            if check:
                template_source = env.loader.get_source(env, file)[0]
                parsed_content = env.parse(template_source)
                variables = meta.find_undeclared_variables(parsed_content)
                diff = list(variables.difference(set(params)))
                if len(diff) > 0:
                    logger.error(f"Missing template parameters: {diff}")
                    raise TemplateParameterException(f"Missing template parameters: {diff}")

            template = env.get_template(file)
            config = template.render(params)
            return config
        except CurcumaException as e:
            logger.error(e)
            sys.exit(1)


class AzureKeyvault:
    """
    Azure Key Vault credential store.

    Provides methods to retrieve secrets from Azure Key Vault.

    Args:
        name (str): The name of the Azure Key Vault.
        tenant_id (str): The Azure tenant ID.
        client_id (str): The Azure client ID.
        client_secret (str): The Azure client secret.
    """

    def __init__(self, name: str, tenant_id: str, client_id: str, client_secret: str):
        """
        Initialize the AzureKeyvault instance.

        Args:
            name (str): The name of the Azure Key Vault.
            tenant_id (str): The Azure tenant ID.
            client_id (str): The Azure client ID.
            client_secret (str): The Azure client secret.
        """
        self.name = name
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.logger = get_logger(name)

    def get_secret(self, name: str):
        """
        Retrieve a secret from Azure Key Vault.

        Args:
            name (str): The name of the secret.

        Returns:
            str: The secret value.
        """
        # Packages providing functionality to get secrets from azure keyvault
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        # The following environment variables are required by the azure.identity library
        # - AZURE_TENANT_ID
        # - AZURE_CLIENT_ID
        # - AZURE_CLIENT_SECRET
        # alternative it will use a 'az login' on the cli
        if self.tenant_id:
            os.environ["AZURE_TENANT_ID"] = self.tenant_id
        if self.client_id:
            os.environ["AZURE_CLIENT_ID"] = self.client_id
        if self.client_secret:
            os.environ["AZURE_CLIENT_SECRET"] = self.client_secret

        self.logger.debug("Initializing azure secret client")
        client = SecretClient(
            vault_url=f"https://{self.name}.vault.azure.net/",
            credential=DefaultAzureCredential(),
        )
        self.logger.info(f"Reading secret '{name}' from azure keyvault")
        secret = client.get_secret(name)
        self.logger.debug("done")
        return secret.value
