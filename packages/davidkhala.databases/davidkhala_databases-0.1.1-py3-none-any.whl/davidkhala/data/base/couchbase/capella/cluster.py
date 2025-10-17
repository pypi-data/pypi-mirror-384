import time
from abc import abstractmethod

from davidkhala.data.base.couchbase.capella.http import API

Status = {
    'stopped': 'turnedOff',
    'started': 'healthy',
    'starting': 'turningOn',
    'stopping': 'turningOff',
    'rebalancing': 'rebalancing'  # under data distributing. e.g. loading sample bucket
}


class AbstractOperator:
    @abstractmethod
    def start(self):
        ...

    @abstractmethod
    def stop(self):
        ...

    @abstractmethod
    def get(self):
        ...

    def wait_until(self, expected, interval=10):

        while True:
            data = self.get()
            currentState = data['currentState']
            if currentState != expected:
                time.sleep(interval)
            else:
                break

        return data

    def ensure_stopped(self):
        data = self.get()
        currentState = data['currentState']
        if currentState == Status['started']:
            self.stop()
        if currentState in [Status['started'], Status['stopping']]:
            self.wait_until(Status['stopped'])
        return data

    def ensure_started(self):
        data = self.get()
        currentState = data['currentState']
        if currentState == Status['stopped']:
            self.start()
        if currentState in [Status['starting'], Status['stopped']]:
            self.wait_until(Status['started'])
        return data


class Cluster:
    def __init__(self, api_secret, organization_id, project_id):
        self.api = API(f"/{organization_id}/projects/{project_id}/clusters", api_secret)
        self.organization_id = organization_id
        self.project_id = project_id

    def list(self):
        return self.api.get()['data']

    class Operator(AbstractOperator):
        def __init__(self, api_secret, organization_id, project_id, cluster_id):
            self.data: dict = {}
            self.api = API(f"/{organization_id}/projects/{project_id}/clusters/{cluster_id}", api_secret)
            self.organization_id = organization_id
            self.project_id = project_id
            self.cluster_id = cluster_id
            self.turnOnLinkedAppService = True

        @property
        def domain(self):
            return self.data['connectionString']

        @property
        def appService(self):
            return self.data['appServiceId']

        @property
        def appServiceOperator(self):
            # TODO
            return AppService.Operator(self.api.secret, self.organization_id, self.project_id, self.cluster_id,
                                       self.appService)

        def start(self):
            self.api.post('/activationState', json={'turnOnLinkedAppService': self.turnOnLinkedAppService})

        def stop(self):
            self.api.delete('/activationState')

        def get(self):
            self.data = self.api.get()
            return self.data


class AppService:
    def __init__(self, api_secret, organization_id):
        self.api = API(f"{organization_id}/appservices", api_secret)

    def list(self):
        return self.api.get()['data']

    class Operator(AbstractOperator):

        def __init__(self, api_secret, organization_id, project_id, cluster_id, appservice_id):
            self.api = API(
                f"/{organization_id}/projects/${project_id}/clusters/${cluster_id}/appservices/${appservice_id}",
                api_secret)
            self.data: dict = {}

        def stop(self):
            self.api.delete('/activationState')

        def get(self):
            self.data = self.api.get('')

        def start(self):
            self.api.post('/activationState')
