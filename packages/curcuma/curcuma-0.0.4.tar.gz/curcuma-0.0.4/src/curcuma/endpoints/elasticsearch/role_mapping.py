# https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-security-put-role-mapping

import re

from loguru import logger

from ...endpoint import Endpoint
from ...exceptions import NotFoundException


class RoleMapping(Endpoint):
    BASE_URL = "/_security/role_mapping"

    def get(self, name: str):
        return self._get(f"{RoleMapping.BASE_URL}/{name}")

    def get_all(self):
        return self._get(RoleMapping.BASE_URL)

    def list(self, filter: str = None):
        pattern = re.compile(filter) if filter else None
        r = self.get_all()
        for name in sorted(r.keys()):
            if pattern and not pattern.search(name):
                continue
            try:
                print(f"Mapping: {name}, Roles: {r[name]['roles']}, Rules: {r[name]['rules']}")
            except KeyError:
                print(f"Mapping: {name}, Template: {r[name]['role_templates']}")

    def set(self, name: str, data: dict):
        self.logger.info(f'Setting role mapping "{name}"')
        self._put(f"{RoleMapping.BASE_URL}/{name}", json=data)

    def set_with_template(self, name: str, template_name: str, template_params: dict = None):
        body = self._render_template("elasticsearch/role_mapping", template_name, template_params)
        self.set(name, body)

    def delete(self, name: str):
        self.logger.info(f"Deleting role mapping '{name}'")
        try:
            self._delete(f"{RoleMapping.BASE_URL}/{name}")
        except NotFoundException:
            pass
