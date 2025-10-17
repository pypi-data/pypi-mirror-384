import unittest
from unittest.mock import patch, Mock
from producteca.sales_orders.sales_orders import SaleOrder
from producteca.client import ProductecaClient


class TestSaleOrder(unittest.TestCase):

    def setUp(self):
        self.client = ProductecaClient(token="test_client", api_key="test_secret")
        self.sale_order_id = 123
        self.mock_response = {
            "id": self.sale_order_id,
            "contact": {"id": 1, "name": "Test Contact"},
            "lines": [],
            "invoiceIntegration": {
                'id': 1,
                'integrationId': 'test-integration',
                'app': 1,
                'createdAt': '2023-01-01',
                'decreaseStock': True
            }
        }

    @patch('requests.get')
    def test_get_sale_order(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: self.mock_response
        )

        sale_order = self.client.SalesOrder.get(self.sale_order_id)
        self.assertEqual(sale_order.id, self.sale_order_id)
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_get_shipping_labels(self, mock_get):
        mock_labels = ["label1", "label2"]
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: mock_labels
        )

        labels = self.client.SalesOrder(id=1234, invoiceIntegration={
                'id': 1,
                'integrationId': 'test-integration',
                'app': 1,
                'createdAt': '2023-01-01',
                'decreaseStock': True,
                "documentUrl": "https://aallala.copm",
                "xmlUrl": "https://aallala.copm",
            }).get_shipping_labels()
        self.assertEqual(labels, mock_labels)
        mock_get.assert_called_once()

    @patch('requests.post')
    def test_close_sale_order(self, mock_post):
        mock_post.return_value = Mock(
            status_code=200
        )

        self.client.SalesOrder(id=1234, invoiceIntegration={
                'id': 1,
                'integrationId': 'test-integration',
                'app': 1,
                'createdAt': '2023-01-01',
                'decreaseStock': True,
                "documentUrl": "https://aallala.copm",
                "xmlUrl": "https://aallala.copm",
            }).close()
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_cancel_sale_order(self, mock_post):
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {"status": "cancelled"}
        )

        self.client.SalesOrder(id=1234, invoiceIntegration={
                'id': 1,
                'integrationId': 'test-integration',
                'app': 1,
                'createdAt': '2023-01-01',
                'decreaseStock': True,
                "documentUrl": "https://aallala.copm",
                "xmlUrl": "https://aallala.copm",
            }).cancel()
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_synchronize_sale_order(self, mock_post):
        sale_order = SaleOrder(**self.mock_response)
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: self.mock_response
        )

        response = self.client.SalesOrder(**sale_order.model_dump(by_alias=True)).synchronize()
        self.assertEqual(response.id, self.sale_order_id)
        mock_post.assert_called_once()

    @patch('requests.put')
    def test_invoice_integration(self, mock_put):
        invoice_data = {
                'id': 1,
                'integrationId': 'test-integration',
                'app': 1,
                'createdAt': '2023-01-01',
                'decreaseStock': True,
                "documentUrl": "https://aallala.copm",
                "xmlUrl": "https://aallala.copm",
            }

        mock_put.return_value = Mock(
            status_code=200,
            json=lambda: invoice_data,
            ok=True
        )

        response = self.client.SalesOrder(id=self.sale_order_id, invoiceIntegration=invoice_data).invoice_integration()
        self.assertTrue(response)
        mock_put.assert_called_once()


if __name__ == '__main__':
    unittest.main()
