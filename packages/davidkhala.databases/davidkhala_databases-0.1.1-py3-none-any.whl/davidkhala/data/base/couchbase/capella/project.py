from davidkhala.data.base.couchbase.capella.http import API
class Project:
    def __init__(self, api_secret, organization_id):
        self.api = API(f"/{organization_id}/projects", api_secret)
    def list(self):
        return self.api.get()['data']