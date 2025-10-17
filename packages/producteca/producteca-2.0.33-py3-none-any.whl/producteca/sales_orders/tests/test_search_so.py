import unittest
import json
from unittest.mock import patch, Mock
from producteca.sales_orders.search_sale_orders import SearchSalesOrderParams, SalesOrderResultItem
from producteca.client import ProductecaClient


class TestSearchSalesOrder(unittest.TestCase):

    def setUp(self):
        self.client = ProductecaClient(token="test_client_id", api_key="test_client_secret")
        self.params = SearchSalesOrderParams(
            top=10,
            skip=0,
            filter="status eq 'confirmed'"
        )

    @patch('requests.get')
    def test_search_saleorder_success(self, mock_get):
        # Mock successful response
        mock_response = Mock()
        with open('producteca/sales_orders/tests/search.json', 'r') as f:
            results = json.loads(f.read())
            mock_response.json.return_value = results
            mock_response.status_code = 200
            mock_get.return_value = mock_response

        response = self.client.SalesOrder.search(self.params)

        self.assertEqual(response.count, 0)
        self.assertEqual(len(response.results), 1)
        self.assertEqual(response.results[0].id, "string")
        self.assertIsInstance(response.results[0], SalesOrderResultItem)

    @patch('requests.get')
    def test_search_saleorder_error(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {"error": "Invalid request"}
        mock_response.status_code = 400
        mock_get.return_value = mock_response
        with self.assertRaises(Exception):
            self.client.SalesOrder.search(self.params)


if __name__ == '__main__':
    unittest.main()
