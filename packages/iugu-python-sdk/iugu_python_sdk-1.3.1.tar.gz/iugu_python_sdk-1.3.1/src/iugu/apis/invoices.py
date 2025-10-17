import logging, jsonpickle
from http import HTTPMethod
from fmconsult.utils.url import UrlUtil
from iugu.api import IuguApi
from iugu.dtos.invoice import Invoice

class Invoices(IuguApi):
    def __init__(self):
        super().__init__()
        self.endpoint_url = UrlUtil().make_url(self.base_url, ['v1', 'invoices'])
    
    def create(self, data:Invoice):
        try:
            logging.info(f'generating invoice...')
            res = self.call_request(HTTPMethod.POST, self.endpoint_url, None, payload=data.to_dict())
            return jsonpickle.decode(res)
        except:
            raise
    
    def cancel(self, id):
        try:
            logging.info(f'delete invoice by id: {id}...')
            endpoint_url = UrlUtil().make_url(self.endpoint_url, [id,'cancel'])
            response = self.call_request(HTTPMethod.PUT, endpoint_url)
            return jsonpickle.decode(response)
        except:
            raise

    def get_by_id(self, id):
        logging.info(f'get invoice info by id: {id}...')
        endpoint_url = UrlUtil().make_url(self.endpoint_url, [id])
        response = self.call_request(HTTPMethod.GET, endpoint_url)
        return jsonpickle.decode(response)

    def mark_invoice_as_paid_externally(self, id, external_payment_id, external_payment_description=None):
        logging.info(f'mark invoice as paid externally by id: {id}...')
        endpoint_url = UrlUtil().make_url(self.endpoint_url, [id, 'externally_pay'])
        
        payload = {
            'external_payment_id': external_payment_id
        }
        
        if not(external_payment_description is None):
            payload['external_payment_description'] = external_payment_description

        response = self.call_request(HTTPMethod.PUT, endpoint_url, None, payload=payload)
        return jsonpickle.decode(response)