# https://www.elastic.co/docs/api/doc/elasticsearch/group/endpoint-ilm

import re

from ...endpoint import Endpoint


class IndexLifecycleManagement(Endpoint):
    BASE_URL = "/_ilm/"

    def get(self):
        return self._get(IndexLifecycleManagement.BASE_URL + "policy/")

    def list(self, filter=None):
        pattern = re.compile(filter) if filter else None
        r = self.get()
        for name in sorted(r.keys()):
            if pattern and not pattern.search(name):
                continue
            try:
                print(f"\nPolicy: {name}")
                for phase in r[name]["policy"]["phases"]:
                    print(f"  Phase: {phase}  Minimum Age: {r[name]["policy"]['phases'][phase]['min_age']}")
                    for action in r[name]["policy"]["phases"][phase]["actions"]:
                        print(f"    Action: {action}")
                        for key, value in r[name]["policy"]["phases"][phase]["actions"][action].items():
                            print(f"      {key}: {value}")
                print("  in_use_by:")
                for key, value in r[name]["in_use_by"].items():
                    if len(value) == 0:
                        continue
                    print(f"    {key}: {value}")
            except KeyError as e:
                print(f"Policy: {name}, Error: {e}")
                print(f"Response: {r[name]}")

    def create(self, name, body):
        self._put(IndexLifecycleManagement.BASE_URL + "policy/" + name, json=body)

    def delete(self, name):
        self._delete(IndexLifecycleManagement.BASE_URL + "policy/" + name)

    def status(self):
        return self._get(IndexLifecycleManagement.BASE_URL + "_status")
