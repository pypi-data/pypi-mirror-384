from davidkhala.data.base.couchbase.capella.http import API


class Organization:
    def __init__(self, api_secret):
        self.api = API('', api_secret)

    def list(self):
        return self.api.get()['data']

    def get(self, organization_id):
        return self.api.get(f"/{organization_id}")


