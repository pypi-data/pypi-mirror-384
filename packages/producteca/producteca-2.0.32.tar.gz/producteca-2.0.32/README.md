[![Maintainability](https://qlty.sh/badges/950972cf-31e6-47cb-ab37-0ad0565c3a59/maintainability.svg)](https://qlty.sh/gh/ChromaAgency/projects/producteca_python)
[![Code Coverage](https://qlty.sh/badges/950972cf-31e6-47cb-ab37-0ad0565c3a59/test_coverage.svg)](https://qlty.sh/gh/ChromaAgency/projects/producteca_python)
[![Test](https://github.com/ChromaAgency/producteca_python/actions/workflows/ci-cd.yml/badge.svg?branch=main)](https://github.com/ChromaAgency/producteca_python/actions/workflows/ci-cd.yml)

# Producteca

This is a small module, to make requests to Producteca API. 

## Install for development

First of all, you need to install [Poetry, follow the instructions here](https://python-poetry.org/docs/#installation).

Once installed, run `poetry install` to install the dependencies.

## Usage

To use the Producteca client, first instantiate `ProductecaClient` with your credentials or add it directly to your env with PRODUCTECA_TOKEN and PRODUCTECA_API_KEY:

```python
from producteca.client import ProductecaClient

client = ProductecaClient(token='your_token', api_key='your_api_key')

# Usage examples for SalesOrderService
sale_order_service = client.SalesOrder
# Get from api
sale_order = sale_order_service.get(123)
# or construct from db
sale_order = client.SalesOrder(...argswithid)
labels = sale_order.get_shipping_labels()
close_response = sale_order.close()
cancel_response = sale_order.cancel()
synchronized_order = sale_order.synchronize()
invoice_response = sale_order.invoice_integration(sale_order)
search_results = sale_order_service.search(params)
payment = sale_order.add_payment(payment_payload)
updated_payment = sale_order.update_payment(payment_id, payment_payload)
shipment = sale_order.add_shipment(shipment_payload)
updated_shipment = sale_order.update_shipment(shipment_id, shipment_payload)

# Usage examples for ProductService
product_service = client.Products
# Get from api
product = product_service.get(456)
bundle = product_service.get_bundle(456)
ml_integration = product_service.get_ml_integration(456)
search_results = product_service.search(search_params)
# Or construct from db
product = client.Products(...args)
created_product = product.create()
updated_product = product.update()
```

then with the client you should use every other module, like SalesOrder, Products, Payments, Shipments and Search


## Contributing

We welcome contributions to improve this project! Here's how you can help:

### Development Setup

1. Fork the repository
2. Clone your fork locally
3. Create a new branch for your feature/fix
4. Make your changes
5. Run tests to ensure everything works
6. Submit a pull request

### Code Style

- Follow PEP 8 guidelines
- Write meaningful commit messages
- Add tests for new features
- Update documentation as needed

### Reporting Issues

If you find a bug or have a feature request:

1. Check existing issues first
2. Create a new issue with:
   - Clear description
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Version information

### Questions?

Feel free to open an issue for any questions about contributing.
