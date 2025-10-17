import logging, jsonpickle
from http import HTTPMethod
from fmconsult.utils.url import UrlUtil
from iugu.api import IuguApi
from iugu.dtos.customer import Customer

class Customers(IuguApi):
    def __init__(self):
        super().__init__()
        self.endpoint_url = UrlUtil().make_url(self.base_url, ['v1', 'customers'])
    
    def create(self, data:Customer):
        try:
            logging.info(f'generating customer...')
            res = self.call_request(HTTPMethod.POST, self.endpoint_url, None, payload=data.to_dict())
            return jsonpickle.decode(res)
        except:
            raise
    
    def update(self, id, data:Customer):
        try:
            logging.info(f'updating customer...')
            endpoint_url = UrlUtil().make_url(self.endpoint_url, [id])
            res = self.call_request(HTTPMethod.PUT, endpoint_url, None, payload=data.to_dict())
            return jsonpickle.decode(res)
        except:
            raise
    
    def get_by_id(self, id):
        logging.info(f'get customer info by id: {id}...')
        endpoint_url = UrlUtil().make_url(self.endpoint_url, [id])
        response = self.call_request(HTTPMethod.GET, endpoint_url)
        return jsonpickle.decode(response)
    
    def remove(self, id):
        try:
            logging.info(f'delete customer by id: {id}...')
            endpoint_url = UrlUtil().make_url(self.endpoint_url, [id])
            response = self.call_request(HTTPMethod.DELETE, endpoint_url)
            return jsonpickle.decode(response)
        except:
            raise