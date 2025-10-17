import base64
import time

from davidkhala.data.base.couchbase.capella.cluster import Cluster, Status
from davidkhala.data.base.couchbase.capella.http import API


def calculateId(name: str) -> str:
    return base64.b64encode(name.encode('utf-8')).decode('utf-8')


class Sample:
    name = {
        'travel': 'travel-sample', 'game': 'gamesim-sample', 'beer': 'beer-sample'
    }

    def __init__(self, api_secret, organization_id, project_id, cluster_id):
        self.api = API(f"/{organization_id}/projects/{project_id}/clusters/{cluster_id}/sampleBuckets", api_secret)
        self.organization_id = organization_id
        self.project_id = project_id
        self.cluster_id = cluster_id

    def preset(self, *names):
        if len(names) == 0:
            existing_names = self.existing()
            names = [s for s in Sample.name.values() if s not in existing_names]
        for name in names:
            yield self.load(name, 10)

    def load(self, name, interval):
        operator = Cluster.Operator(self.api.secret, self.organization_id, self.project_id, self.cluster_id)
        operator.wait_until(Status['started'])
        self.api.post('', json={
            'name': name
        })
        while True:
            count = self.get(name)['stats']['itemCount']
            if count < 2:
                time.sleep(interval)
            else:
                break

    def existing(self):
        return list(map(lambda x:x['name'], self.list()))

    def list(self):
        return self.api.get()['data']
    def get(self, name):
        bucket_id = calculateId(name)

        return self.api.get(f"/{bucket_id}")
