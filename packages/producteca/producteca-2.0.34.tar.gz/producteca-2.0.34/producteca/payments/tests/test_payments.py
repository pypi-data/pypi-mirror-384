import unittest
from unittest.mock import patch, Mock
from datetime import datetime
from producteca.client import ProductecaClient
from producteca.payments.payments import Payment


class TestPayments(unittest.TestCase):
    def setUp(self):
        self.client = ProductecaClient(token="asd", api_key="test_key")
        self.sale_order_id = 123
        self.payment_id = 456
        
        self.payment_data = {
            "date": datetime.now().isoformat(),
            "amount": 100.0,
            "status": "approved",
            "method": "credit_card",
            "hasCancelableStatus": True,
            "card": {
                "paymentNetwork": "visa",
                "firstSixDigits": 123456,
                "lastFourDigits": 7890
            }
        }
        
    @patch('requests.post')
    def test_create_payment(self, mock_post):
        # Prepare mock response
        mock_response = Mock()
        mock_response.json.return_value = self.payment_data
        mock_post.return_value = mock_response
        
        # Create payment object
        payment = Payment(**self.payment_data)
        
        # Test create method
        result = self.client.SalesOrder(id=self.sale_order_id, invoiceIntegration={
                'id': 1,
                'integrationId': 'test-integration',
                'app': 1,
                'createdAt': '2023-01-01',
                'decreaseStock': True,
                "documentUrl": "https://aallala.copm",
                "xmlUrl": "https://aallala.copm",
            }).add_payment(payment.model_dump(by_alias=True))
        
        # Assertions
        mock_post.assert_called_once()
        self.assertEqual(result.amount, 100.0)
        self.assertEqual(result.status, "approved")
        self.assertEqual(result.method, "credit_card")
        self.assertTrue(result.hasCancelableStatus)
        
    @patch('requests.put')
    def test_update_payment(self, mock_put):
        # Prepare mock response
        mock_response = Mock()
        mock_response.json.return_value = self.payment_data
        mock_put.return_value = mock_response
        
        # Create payment object for update
        payment = Payment(**self.payment_data)
        
        # Test update method
        result = self.client.SalesOrder(id=self.sale_order_id, invoiceIntegration={
                'id': 1,
                'integrationId': 'test-integration',
                'app': 1,
                'createdAt': '2023-01-01',
                'decreaseStock': True,
                "documentUrl": "https://aallala.copm",
                "xmlUrl": "https://aallala.copm",
            }).update_payment(self.payment_id, payment.model_dump(by_alias=True))
        
        # Assertions
        mock_put.assert_called_once()
        self.assertEqual(result.amount, 100.0)
        self.assertEqual(result.status, "approved")
        self.assertEqual(result.method, "credit_card")
        self.assertTrue(result.hasCancelableStatus)


if __name__ == '__main__':
    unittest.main()
