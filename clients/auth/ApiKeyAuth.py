from BaseAuth import BaseAuth

class ApiKeyAuth(BaseAuth):
    def __init__(self, api_key):
        self.api_key = api_key

    def authenticate(self, headers):
        """Devuelve un diccionario de headers con la API Key"""
        headers['X-API-KEY'] = self.api_key
        return headers