# pylint: disable=W1203,W0621,W0123,W0718

from ...endpoint import Endpoint


class AdvancedSettings(Endpoint):
    BASE_URL = "/s/{space}/api/kibana/settings"

    def get(self, space: str):
        self.logger.info(f"Reading advanced settings from space '{space}'")
        return self._get(self.BASE_URL.format(space=space))

    def set(self, space: str, changes: dict[str, str | int | bool]):
        cur = self.get(space).get("settings")
        self.logger.info(f"Changing advanced settings in space '{space}'")
        for param, value in changes.items():
            if param in cur:
                if cur.get(param).get("userValue") == value:
                    self.logger.debug(f"'{param}' is up-to-date")
                else:
                    self.logger.debug(f"changing '{param}' from '{cur.get(param).get('userValue')}' to '{value}'")
            else:
                if value is None:
                    self.logger.debug(f"'{param}' is up-to-date")
                else:
                    self.logger.debug(f"setting '{param}' to '{value}'")
        body = {"changes": changes}
        self._post(self.BASE_URL.format(space=space), json=body)
