import json
import time
from enum import Enum

import httpx

from ...endpoint import Endpoint
from ...exceptions import NotFoundException
from ...log import get_logger

logger = get_logger(__name__)


class DeploymentAPI(Endpoint):
    BASE_URL = "/api/v1/deployments"

    def get_deployment(self, deployment_id: str):
        return Deployment(self, self.get(deployment_id))

    def get_deployment_by_name(self, deployment_name: str):
        logger.debug('Looking for a deployment with name "%s"', deployment_name)
        for d in self.get_all().get("deployments"):
            logger.debug("deployment name: %s  id: %s", d.get("name"), d.get("id"))
            if d.get("name") == deployment_name:
                logger.debug("deployment found")
                return Deployment(self, d)
        logger.error('no deployment with the name "%s" found', deployment_name)
        raise NotFoundException(f'no deployment with the name "{deployment_name}" found')

    def get_all(self) -> dict:
        logger.info("Reading deployments")
        return self._get(DeploymentAPI.BASE_URL)

    def get(self, deployment_id: str, deployment_name: str = None) -> dict:
        logger.info('Reading deployment "%s"', deployment_name if deployment_name else deployment_id)
        return self._get(f"{DeploymentAPI.BASE_URL}/{deployment_id}?clear_transient=true")

    def list(self):
        r = self.get_all()
        for deployment in r.get("deployments"):
            print(f"Name: {deployment.get('name')}")
            print(json.dumps(deployment, indent=2))

    # @staticmethod
    # def _quote_if_string(value: str):
    #     return value if isinstance(value, int) or value.isdigit() else f"'{value}'"

    # def create(self, template_name: str, template_params):
    #     logger.debug(f'Using template "{template_name}" and params "{template_params}" for deployment')
    #     config = self._render_template(
    #         "cloud/deployment", template_name.replace("aws-", ""), template_params, check=False
    #     )
    #     logger.info(f'Creating deployment "{template_params["cluster_name"]}"')
    #     logger.debug(f'using config: "{config}"')
    #     self._post(
    #         DeploymentAPI.BASE_URL + f"?template_id={template_name}&validate_only=true",
    #         config,
    #     )

    def create_with_template(self, template_name: str, template_params: dict = None):
        logger.debug('Using template "%s" and params "%s" for deployment', template_name, template_params)
        config = self._render_template("cloud/deployment", template_name, template_params, check=False)
        logger.info('Creating deployment "%s"', template_params["cluster_name"])
        logger.debug('using config: "%s"', config)
        # template = self._get_template(template_name)
        # for key, value in template_params.items():
        #     exec(
        #         f"template[{"][".join(Deployment._quote_if_string(k) for k in key.split("."))}] = {Deployment._quote_if_string(value)}"
        #     )
        r = self._post(DeploymentAPI.BASE_URL + "?validate_only=false", config)
        print(r)
        logger.info("Deployment-ID: %s", r.get("id"))
        return Deployment(self, r.get("id"))

    def update(self, deployment_id: str, config: dict):
        cur_conf = self.get(deployment_id)
        logger.info('Updating deployment "%s"', cur_conf["name"])
        logger.debug('using config: "%s"', config)
        self._deepdiff(cur_conf, config)
        return self._put(DeploymentAPI.BASE_URL + f"/{deployment_id}", config)

    def update_with_template(self, deployment_id: str, template_name: str, template_params: dict = None):
        logger.debug('Using template "%s" and params "%s" for deployment', template_name, template_params)
        config = self._render_template("cloud/deployment", template_name, template_params, check=False)
        cur_conf = self.get(deployment_id)
        logger.info('Updating deployment "%s"', template_params["cluster_name"])
        logger.debug('using config: "%s"', config)
        self._deepdiff(cur_conf, config)
        return self._put(DeploymentAPI.BASE_URL + f"/{deployment_id}", config)

    def reset_password(self, deployment_id: str, ref_id: str):
        logger.info('Resetting password for deployment id "%s"', deployment_id)
        r = self._post(DeploymentAPI.BASE_URL + f"/{deployment_id}/elasticsearch/{ref_id}/_reset-password")
        return r.get("password")

    def delete(self, deployment_id):
        logger.info('Deleting deployment "%s"', deployment_id)
        self._post(DeploymentAPI.BASE_URL + f"/{deployment_id}/_shutdown?skip_snapshot=true")

    def _list_cloud_templates(self, region: str):
        r = self._get(DeploymentAPI.BASE_URL + f"/templates?region={region}&hide-deprecated=true")
        for template in r:
            print(f"Name: {template.get('name')}  ID: {template.get('id')}  Description: {template.get('description')}")

    def _get_cloud_template(self, template_name: str, region: str):
        r = self._get(DeploymentAPI.BASE_URL + f"/templates/{template_name}?region={region}")
        print(r)
        return r.get("deployment_template")


class Deployment(Endpoint):
    def __init__(self, api: DeploymentAPI, deployment: dict):
        self._api = api
        self.id = deployment.get("id")
        self.name = deployment.get("name")
        self.alias = deployment.get("alias")
        self.logger = get_logger(self.name)
        super().__init__(api._clt, self.name)

    @property
    def keystore(self):
        return Deployment.Keystore(self._clt, self)

    def config(self):
        return self._api.get(self.id)

    def info(self, instance: "Deployment.Instance", ref_id: str = "_main"):
        response = self._get(
            f"{DeploymentAPI.BASE_URL}/{self.id}/{instance.value}/{ref_id}?show_plans=false&clear_transient"
        )
        return response.get("info")
        # return {
        #     "healthy": r["info"]["healthy"],
        #     "status": r["info"]["status"],
        #     "elasticsearch": {
        #         "healthy": r["info"]["elasticsearch"]["healthy"],
        #         "shard_info": r["info"]["elasticsearch"]["shard_info"],
        #         "shards_status": r["info"]["elasticsearch"]["shards_status"]["status"],
        #     },
        # }

    def restart(self, wait: bool = False):
        self.logger.warning("restarting the deployment")
        self._post(DeploymentAPI.BASE_URL + f"/{self.id}/elasticsearch/_main/_restart")
        status = "unknown"
        if wait:
            self.logger.info("waiting for availability...")
            while status != "started":
                time.sleep(5)
                try:
                    status = self.info(Deployment.Instance.Elasticsearch).get("info").get("status")
                except httpx.ReadTimeout:
                    pass
                self.logger.debug("current status: %s", status)
            self.logger.debug("done")

    def status(self):
        info = self.info(Deployment.Instance.Elasticsearch)
        return {
            "healthy": info["healthy"],
            "status": info["status"],
            "elasticsearch": {
                "healthy": info["elasticsearch"]["healthy"],
                "shard_info": info["elasticsearch"]["shard_info"],
                "shards_status": info["elasticsearch"]["shards_status"]["status"],
            },
        }

    def reset_password(self):
        print(self._api.reset_password(self.id, "es-ref-id"))

    def update(self, config: dict):
        self._api.update(self.id, config)

    def update_with_template(self, template_name: str, template_params: dict = None):
        self._api.update_with_template(self.id, template_name, template_params)

    def delete(self):
        logger.info('Deleting deployment "%s"', self.name)
        self._api.delete(self.id)

    class Keystore(Endpoint):

        def __init__(self, client, deployment):
            ref_id = "_main"
            self.BASE_URL = f"/api/v1/deployments/{deployment.id}/elasticsearch/{ref_id}/keystore"
            super().__init__(client)
            self.logger = get_logger(deployment.name)

        def get(self) -> dict:
            self.logger.info("Reading keystore")
            return self._get(self.BASE_URL)

        def add_api_key(self, alias: str, value: str) -> dict:
            self.logger.info("Writing alias '%s' to keystore", alias)
            return self._patch(
                self.BASE_URL, json={"secrets": {f"cluster.remote.{alias}.credentials": {"value": value}}}
            )

        def add_security_key(self, key: str, value: str) -> dict:
            self.logger.info("Writing security key '%s' to keystore", key)
            return self._patch(self.BASE_URL, json={"secrets": {key: {"value": value}}})

    class Instance(Enum):
        APM = "apm"
        AppSearch = "appsearch"
        Elasticsearch = "elasticsearch"
        EnterpriseSearch = "enterprise_search"
        IntegrationsServer = "integrations_server"
        Kibana = "kibana"
