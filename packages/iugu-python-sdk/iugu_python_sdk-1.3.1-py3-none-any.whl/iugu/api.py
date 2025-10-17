import os, base64
from fmconsult.http.api import ApiBase

class IuguApi(ApiBase):

    def __init__(self):
        try:
            self.api_token = os.environ['iugu.api.token']
            self.api_environment = os.environ['iugu.api.environment']
            
            self.base_url = 'https://api.iugu.com'

            token_bytes = f'{self.api_token}:'.encode('utf-8')
            basic_token = base64.b64encode(token_bytes).decode('utf-8')

            self.headers = {
                'Authorization': f'Basic {basic_token}'
            }
        except:
            raise