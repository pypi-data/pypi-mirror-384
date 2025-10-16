import base64

import httpx

from .endpoints.cloud.billing_costs import BillingCosts
from .endpoints.cloud.deployment import DeploymentAPI
from .endpoints.cloud.traffic_filter import TrafficFilter

from .endpoints.elasticsearch.api_key import ApiKey
from .endpoints.elasticsearch.api_key import CrossClusterApiKey
from .endpoints.elasticsearch.ilm import IndexLifecycleManagement
from .endpoints.elasticsearch.index_alias import IndexAlias
from .endpoints.elasticsearch.role_mapping import RoleMapping
from .endpoints.elasticsearch.snapshot import Snapshot

from .endpoints.kibana.data_view import DataView
from .endpoints.kibana.role import Role
from .endpoints.kibana.space import Space
from .endpoints.kibana.settings import AdvancedSettings

from .config import Config


class Client:

    def __init__(
        self,
        cluster_name: str,
        elasticsearch_host: str = None,
        kibana_host: str = None,
        port: int = 443,
        username: str = None,
        password: str = None,
        api_key: str = None,
    ):
        authorization = (
            f"ApiKey {api_key}"
            if api_key is not None
            else f"Basic {base64.b64encode(bytes(username + ":" + password, 'utf-8')).decode('utf-8')}"
        )
        self.cluster_name = cluster_name
        self.es = Client.ElasticSearch(elasticsearch_host, port, authorization)
        self.kb = Client.Kibana(kibana_host, port, authorization)

    class ElasticSearch:
        def __init__(self, host, port, authorization):
            self.host_name = host.split(".")[0]
            self._es = httpx.Client(
                base_url=f"https://{host}:{port}",
                headers=httpx.Headers(
                    {
                        "Content-Type": "application/json",
                        "Authorization": authorization,
                    }
                ),
            )

        @property
        def api_key(self):
            return ApiKey(self._es, self.host_name)

        @property
        def cross_cluster_api_key(self):
            return CrossClusterApiKey(self._es, self.host_name)

        @property
        def role_mapping(self):
            return RoleMapping(self._es, self.host_name)

        @property
        def index_alias(self):
            return IndexAlias(self._es, self.host_name)

        @property
        def ilm(self):
            return IndexLifecycleManagement(self._es, self.host_name)

        @property
        def snapshot(self):
            return Snapshot(self._es, self.host_name)

    class Kibana:
        def __init__(self, host, port, authorization):
            self.host_name = host.split(".")[0]
            self._kb = httpx.Client(
                base_url=f"https://{host}:{port}",
                headers=httpx.Headers(
                    {
                        "Content-Type": "application/json",
                        "Authorization": authorization,
                        "kbn-xsrf": "true",
                    }
                ),
            )

        @property
        def space(self):
            return Space(self._kb, self.host_name)

        @property
        def role(self):
            return Role(self._kb, self.host_name)

        @property
        def data_view(self):
            return DataView(self._kb, self.host_name)

        @property
        def advanced_settings(self):
            return AdvancedSettings(self._kb, self.host_name)


class AzureClient(Client):
    def __init__(
        self,
        cluster_name: str,
        location: str,
        private_link: bool = False,
        api_key: str = None,
        username: str = None,
        password: str = None,
    ):
        super().__init__(
            cluster_name=cluster_name,
            elasticsearch_host=f"{cluster_name}.es{".privatelink" if private_link else ""}.{location}.azure.elastic-cloud.com",
            kibana_host=f"{cluster_name}.kb{".privatelink" if private_link else ""}.{location}.azure.elastic-cloud.com",
            api_key=api_key,
            username=username,
            password=password,
        )

    @classmethod
    def by_config(cls, file: str, params: dict = None):
        config = Config(file, params=params).get_deployment()
        return cls(
            cluster_name=config["alias"] if "alias" in config else config["name"],
            location=config["location"],
            private_link=config["privatelink"],
            api_key=config["api_key"] if "api_key" in config else None,
            username=(
                config["elasticsearch"]["username"] if "username" in config.get("elasticsearch", {}) else "elastic"
            ),
            password=config["elasticsearch"]["password"] if "password" in config.get("elasticsearch", {}) else None,
        )


class CloudClient:
    def __init__(self, api_key: str, organization_id: int = None):
        self._organization_id = organization_id
        self._cld = httpx.Client(
            base_url="https://api.elastic-cloud.com",
            headers=httpx.Headers(
                {
                    "Content-Type": "application/json",
                    "Authorization": f"ApiKey {api_key}",
                }
            ),
        )

    @classmethod
    def by_config(cls, file: str):
        config = Config(file).get_ech()
        return cls(config["api-key"], config.get("organization-id"))

    @property
    def billing_costs(self):
        return BillingCosts(self._cld, self._organization_id)

    @property
    def deployment(self):
        return DeploymentAPI(self._cld)

    @property
    def traffic_filter(self):
        return TrafficFilter(self._cld)

    # shortcuts
    @property
    def bc(self):
        return BillingCosts(self._cld, self._organization_id)

    @property
    def dpl(self):
        return DeploymentAPI(self._cld)

    @property
    def tf(self):
        return TrafficFilter(self._cld)
