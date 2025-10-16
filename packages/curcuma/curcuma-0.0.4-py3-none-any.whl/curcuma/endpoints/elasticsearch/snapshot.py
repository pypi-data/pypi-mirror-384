from ...endpoint import Endpoint


class Snapshot(Endpoint):

    def get_repos(self):
        return self._get("/_snapshot/_all")

    def list(self):
        for repo in self.get_repos():
            print(f"Repository: {repo}")

            r = self._get(f"/_snapshot/{repo}/_all")
            for snapshot in r["snapshots"]:
                print(
                    f"Snapshot: {snapshot['snapshot']}, State: {snapshot['state']}, Start Time: {snapshot['start_time']}, Shards: {snapshot['shards']['total']},  Failed: {snapshot['shards']['failed']}"
                )
