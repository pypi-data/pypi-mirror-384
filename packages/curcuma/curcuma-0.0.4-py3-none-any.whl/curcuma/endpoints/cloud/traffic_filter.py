import json

from ...endpoint import Endpoint
from ...log import get_logger

logger = get_logger(__name__)


class TrafficFilter(Endpoint):
    BASE_URL = "/api/v1/deployments/traffic-filter/rulesets"

    def get_all(self, region: str = None) -> dict:
        logger.info("Reading deployments" + (f" for region '{region}'" if region else ""))
        return self._get(TrafficFilter.BASE_URL + (f"?region={region}" if region else ""))

    def get(self, type: str, id: str) -> dict:
        logger.info(f'Reading deployment "{id}"')
        return self._get(f"{TrafficFilter.BASE_URL}/{type}/{id}/rulesets")

    def show(self, type: str, id: str):
        print(json.dumps(self.get(type, id), indent=2))

    def list(self, region: str = None, type: str = None, show_config: bool = False):
        r = self.get_all(region)
        for filter in r.get("rulesets"):
            if type and type != filter.get("type"):
                continue
            print(f"Name: {filter.get('name')}  Type: {filter.get('type')}  ID: {filter.get('id')}")
            if show_config:
                print(json.dumps(filter, indent=2))

    # def create_by_template(self, template_name: str, template_params: dict = {}):
    #     logger.debug(
    #         f'Using template "{template_name}" and params "{template_params}" for deployment'
    #     )
    #     config = self._render_template("role", template_name, template_params)
    #     self._post(TrafficFilter.BASE_URL, config)
