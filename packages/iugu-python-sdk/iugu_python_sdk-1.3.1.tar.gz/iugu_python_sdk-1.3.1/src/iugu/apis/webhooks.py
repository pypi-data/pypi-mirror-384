import logging, jsonpickle
from http import HTTPMethod
from fmconsult.utils.url import UrlUtil
from iugu.api import IuguApi
from iugu.dtos.webhook import Webhook

class Webhooks(IuguApi):
    def __init__(self):
        super().__init__()
        self.endpoint_url = UrlUtil().make_url(self.base_url, ['v1', 'web_hooks'])

    def create(self, data:Webhook):
        try:
            logging.info(f'generating webhook...')
            res = self.call_request(HTTPMethod.POST, self.endpoint_url, None, payload=data.to_dict())
            return jsonpickle.decode(res)
        except:
            raise
    
    def update(self, id, data:Webhook):
        try:
            logging.info(f'updating webhook...')
            endpoint_url = UrlUtil().make_url(self.endpoint_url, [id])
            res = self.call_request(HTTPMethod.PUT, endpoint_url, None, payload=data.to_dict())
            return jsonpickle.decode(res)
        except:
            raise

    def get_by_id(self, id):
        logging.info(f'get webhook info by id: {id}...')
        endpoint_url = UrlUtil().make_url(self.endpoint_url, [id])
        response = self.call_request(HTTPMethod.GET, endpoint_url)
        return jsonpickle.decode(response)

    def remove(self, id):
        try:
            logging.info(f'delete webhook by id: {id}...')
            endpoint_url = UrlUtil().make_url(self.endpoint_url, [id])
            response = self.call_request(HTTPMethod.DELETE, endpoint_url)
            return jsonpickle.decode(response)
        except:
            raise