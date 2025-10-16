import requests


class HttpClient:
    def __init__(self):
        self.session = requests.Session()

    def get(self, url, **kwargs):
        response = self.session.get(url, timeout=5, **kwargs)
        return response.status_code, response.content

    def post(self, url, *args, **kwargs):
        response = self.session.post(url, *args, timeout=5, **kwargs)
        return response.status_code, response

    def put(self, url, *args, **kwargs):
        response = self.session.put(url, *args, timeout=5, **kwargs)
        return response.status_code, response
