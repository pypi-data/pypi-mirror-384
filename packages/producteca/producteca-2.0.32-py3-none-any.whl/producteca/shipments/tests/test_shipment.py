import unittest
from unittest.mock import patch, MagicMock
from producteca.shipments.shipment import Shipment, ShipmentProduct, ShipmentMethod, ShipmentIntegration
from producteca.client import ProductecaClient


class TestShipment(unittest.TestCase):
    def setUp(self):
        self.client = ProductecaClient(token="test_id", api_key="test_secret")
        
    @patch('requests.post')
    def test_create_shipment(self, mock_post):
        # Arrange
        products = [ShipmentProduct(product=1, variation=2, quantity=3)]
        method = ShipmentMethod(trackingNumber="TN123", trackingUrl="http://track.url", courier="DHL", mode="air", cost=10.5, type="express", eta=5, status="shipped")
        integration = ShipmentIntegration(id=1, integrationId="int123", app=10, status="active")
        payload = Shipment(date="2023-01-01", products=products, method=method, integration=integration).model_dump(by_alias=True)

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = payload
        mock_post.return_value = mock_response
        # Act
        shipment = self.client.SalesOrder(id=1234, invoiceIntegration={
            'id': 1,
            'integrationId': 'test-integration',
            'app': 1,
            'createdAt': '2023-01-01',
            'decreaseStock': True
        }).add_shipment(payload)

        self.assertIsInstance(shipment, Shipment)
        mock_post.assert_called_once()

    @patch('requests.put')
    def test_update_shipment(self, mock_put):
        # Arrange
        shipment_id = 'abc'
        products = [ShipmentProduct(product=4, quantity=7)]
        method = ShipmentMethod(courier="FedEx", cost=15.0)
        integration = ShipmentIntegration(status="pending")
        payload = Shipment(date="2023-02-02", products=products, method=method, integration=integration).model_dump(by_alias=True)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = payload
        mock_put.return_value = mock_response
        # Act
        shipment = self.client.SalesOrder(id=1234, invoiceIntegration={
            'id': 1,
            'integrationId': 'test-integration',
            'app': 1,
            'createdAt': '2023-01-01',
            'decreaseStock': True
        }).update_shipment(shipment_id, payload)

        self.assertIsInstance(shipment, Shipment)
        mock_put.assert_called_once()


if __name__ == '__main__':
    unittest.main()
