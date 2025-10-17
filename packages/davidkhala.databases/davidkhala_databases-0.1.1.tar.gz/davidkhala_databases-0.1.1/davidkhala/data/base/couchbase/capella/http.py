from davidkhala.utils.http_request import Request

BaseURL = 'https://cloudapi.cloud.couchbase.com/v4/organizations'


class API:
    def __init__(self, group, api_secret):
        self.api = Request({
            'bearer': api_secret
        })
        self.url = BaseURL + group

        self.secret = api_secret

    def get(self, route = '', **kwargs):
        return self.api.request(self.url + route, 'GET', **kwargs)

    def post(self, route= '', **kwargs):
        self.api.request(self.url + route, 'POST', **kwargs)

    def delete(self, route= '', **kwargs):
        self.api.request(self.url + route, 'DELETE', **kwargs)

