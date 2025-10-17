import unittest
from unittest.mock import patch, Mock
from producteca.products.products import Product
from producteca.client import ProductecaClient


class TestProduct(unittest.TestCase):
    def setUp(self):
        self.client = ProductecaClient(token="test_client_id", api_key="test_client_secret")
        self.test_product = Product(
            sku="TEST001",
            name="Test Product",
            code="TEST001",
            category="Test"
        )
        self.product_to_create_payload = {
            "sku": "9817234",
            "code": "871234",
            "name": "Hola test",
            "buyingPrice": 0,
            "deals": [
                {
                "campaign": "string",
                "regularPrice": 0,
                "dealPrice": 0
                }
            ],
                "prices": [
                {
                "amount": 10,
                "currency": "Local",
                "priceList": "Default"
                }
            ],
                "stocks": [
                    {
                    "quantity": 2,
                    "availableQuantity": 2,
                    "warehouse": "Default"
                    }
                ],
            }

    @patch('requests.post')
    def test_create_product_success(self, mock_post):
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.test_product.model_dump()
        mock_post.return_value = mock_response

        response = self.client.Product(**self.test_product.model_dump()).synchronize(self.product_to_create_payload)
        
        self.assertEqual(response.sku, "TEST001")

    @patch('requests.post')
    def test_create_product_not_exist(self, mock_post):
        # Mock product not found response
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        with self.assertRaises(Exception):
            self.client.Product.synchronize(self.product_to_create_payload)

    @patch('requests.post')
    def test_update_product_success(self, mock_post):
        payload = self.product_to_create_payload
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.test_product.model_dump()
        mock_post.return_value = mock_response

        response = self.client.Product(**self.test_product.model_dump()).synchronize(payload)
        
        self.assertEqual(response.name, "Test Product")

    @patch('requests.get')
    def test_get_product(self, mock_get):
        # Mock get product response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.test_product.model_dump()
        mock_get.return_value = mock_response

        response = self.client.Product.get(1)
        
        self.assertEqual(response.sku, "TEST001")

    @patch('requests.get')
    def test_get_bundle(self, mock_get):
        # Mock get bundle response
        mock_response = Mock()
        mock_response.status_code = 200
        test_prod = {
                "results": [
                    {
                    "companyId": 0,
                    "productId": 0,
                    "variations": [
                        {
                        "variationId": 0,
                        "components": [
                            {
                            "quantity": 0,
                            "variationId": 0,
                            "productId": 0
                            }
                        ]
                        }
                    ],
                    "id": "string"
                    }
                ],
                "count": 0
                }
        mock_response.json.return_value = test_prod
        mock_get.return_value = mock_response

        product = self.client.Product.get_bundle(1)
        
        self.assertEqual(product.count, 0)

    @patch('requests.get')
    def test_get_ml_integration(self, mock_get):
        # Mock ML integration response
        mock_response = Mock()
        mock_response.status_code = 200
        meli_product = {
            "hasCustomShippingCosts": True,
            "productId": 0,
            "shipping": {
                "localPickup": True,
                "mode": "string",
                "freeShipping": True,
                "freeShippingCost": 0,
                "mandatoryFreeShipping": True,
                "freeShippingMethod": "string"
            },
            "mShopsShipping": {
                "enabled": True
            },
            "addFreeShippingCostToPrice": True,
            "category": {
                "meliId": "string",
                "acceptsMercadoenvios": True,
                "suggest": True,
                "fixed": True
            },
            "attributeCompletion": {
                "productIdentifierStatus": "Complete",
                "dataSheetStatus": "Complete",
                "status": "Complete",
                "count": 0,
                "total": 0
            },
            "catalogProducts": [
                "string"
            ],
            "warranty": "string",
            "domain": "string",
            "listingTypeId": "GoldSpecial",
            "catalogProductsStatus": "Unlinked",
            "tags": [
                "string"
            ]
            }
        
        mock_response.json.return_value = meli_product
        mock_get.return_value = mock_response

        product = self.client.Product.get_ml_integration(1)
        
        self.assertEqual(product.listing_type_id, "GoldSpecial")


if __name__ == '__main__':
    unittest.main()
