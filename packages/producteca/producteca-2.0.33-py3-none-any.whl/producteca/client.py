from producteca.config.config import ConfigProducteca
from producteca.products.products import ProductService
from producteca.sales_orders.sales_orders import SaleOrderService

import os


class ProductecaClient:

    def __init__(self, token: str = os.environ.get('PRODUCTECA_TOKEN', ''), api_key: str = os.environ.get('PRODUCTECA_API_KEY', '')):
        if not token:
            raise ValueError('PRODUCTECA_TOKEN environment variable not set')
        if not api_key:
            raise ValueError('PRODUCTECA_API_KEY environment variable not set')
        self.config = ConfigProducteca(token=token, api_key=api_key)

    @property
    def Product(self):
        return ProductService(self.config)

    @property
    def SalesOrder(self):
        return SaleOrderService(self.config)

