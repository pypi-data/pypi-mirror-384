import logging, jsonpickle
from http import HTTPMethod
from fmconsult.utils.url import UrlUtil
from iugu.api import IuguApi
from iugu.dtos.subscription import Subscription

class Subscriptions(IuguApi):
    def __init__(self):
        super().__init__()
        self.endpoint_url = UrlUtil().make_url(self.base_url, ['v1', 'subscriptions'])
    
    def create(self, data:Subscription):
        try:
            logging.info(f'generating subscription...')
            res = self.call_request(HTTPMethod.POST, self.endpoint_url, None, payload=data.to_dict())
            return jsonpickle.decode(res)
        except:
            raise
    
    def get_by_id(self, id):
        logging.info(f'get subscription info by id: {id}...')
        endpoint_url = UrlUtil().make_url(self.endpoint_url, [id])
        response = self.call_request(HTTPMethod.GET, endpoint_url)
        return jsonpickle.decode(response)

    def remove(self, id):
        try:
            logging.info(f'delete subscription by id: {id}...')
            endpoint_url = UrlUtil().make_url(self.endpoint_url, [id])
            response = self.call_request(HTTPMethod.DELETE, endpoint_url)
            return jsonpickle.decode(response)
        except:
            raise