from typing import List, Optional, Union
from pydantic import BaseModel, Field, ValidationError
from dataclasses import dataclass
from producteca.abstract.abstract_dataclass import BaseService
from producteca.products.search_products import SearchProduct, SearchProductParams
import logging
import requests

_logger = logging.getLogger(__name__)


class Attribute(BaseModel):
    key: str
    value: str


class Tag(BaseModel):
    tag: str


class Dimensions(BaseModel):
    weight: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    length: Optional[float] = None
    pieces: Optional[int] = None


class Deal(BaseModel):
    campaign: str
    regular_price: Optional[float] = Field(default=None, alias='regularPrice')
    deal_price: Optional[float] = Field(default=None, alias='dealPrice')


class Stock(BaseModel):
    quantity: Optional[int] = None
    available_quantity: Optional[int] = Field(default=None, alias='availableQuantity')
    warehouse: Optional[str] = None
    warehouse_id: Optional[int] = Field(default=None, alias='warehouseId')
    reserved: Optional[int] = None
    available: Optional[int] = None


class Price(BaseModel):
    amount: Optional[float] = None
    currency: str
    price_list: str = Field(alias='priceList')
    price_list_id: Optional[int] = Field(default=None, alias='priceListId')


class Picture(BaseModel):
    url: str


class Integration(BaseModel):
    app: Optional[int] = None
    integration_id: Optional[str] = Field(default=None, alias='integrationId')
    permalink: Optional[str] = None
    status: Optional[str] = None
    listing_type: Optional[str] = Field(default=None, alias='listingType')
    safety_stock: Optional[int] = Field(default=None, alias='safetyStock')
    synchronize_stock: Optional[bool] = Field(default=None, alias='synchronizeStock')
    is_active: Optional[bool] = Field(default=None, alias='isActive')
    is_active_or_paused: Optional[bool] = Field(default=None, alias='isActiveOrPaused')
    id: Optional[int] = None
    parent_integration: Optional[str] = Field(default=None, alias='parentIntegration')


class Variation(BaseModel):
    variation_id: Optional[int] = Field(default=None, alias='variationId')
    components: Optional[List] = None
    pictures: Optional[List[Picture]] = None
    stocks: Optional[List[Stock]] = None
    attributes_hash: Optional[str] = Field(default=None, alias='attributesHash')
    primary_color: Optional[str] = Field(default=None, alias='primaryColor')
    thumbnail: Optional[str] = None
    attributes: Optional[List[Attribute]] = None
    integrations: Optional[List[Integration]] = None
    id: Optional[int] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None


class MeliCategory(BaseModel):
    meli_id: Optional[str] = Field(default=None, alias='meliId')
    accepts_mercadoenvios: Optional[bool] = Field(default=None, alias='acceptsMercadoenvios')
    suggest: Optional[bool] = None
    fixed: Optional[bool] = None


class BundleComponent(BaseModel):
    quantity: int
    variation_id: int = Field(alias='variationId')
    product_id: int = Field(alias='productId')


class BundleVariation(BaseModel):
    variation_id: int = Field(alias='variationId')
    components: List[BundleComponent]


class BundleResult(BaseModel):
    company_id: int = Field(alias='companyId')
    product_id: int = Field(alias='productId')
    variations: List[BundleVariation]
    id: str


class BundleResponse(BaseModel):
    results: List[BundleResult]
    count: int


class Product(BaseModel):
    integrations: Optional[List[Integration]] = None
    variations: Optional[List[Variation]] = None
    is_simple: Optional[bool] = Field(default=None, alias='isSimple')
    has_variations: Optional[bool] = Field(default=None, alias='hasVariations') 
    thumbnail: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None
    prices: Optional[List[Price]] = None
    buying_price: Optional[float] = Field(default=None, alias='buyingPrice')
    is_archived: Optional[bool] = Field(default=None, alias='isArchived')
    dimensions: Optional[Dimensions] = None
    attributes: Optional[List[Attribute]] = None
    metadata: Optional[List[str]] = None
    is_original: Optional[bool] = Field(default=None, alias='isOriginal')
    name: str
    code: Optional[str] = None
    sku: Optional[str] = None
    brand: Optional[str] = None
    id: Optional[int] = None


class ProductVariationBase(BaseModel):
    sku: str
    variation_id: Optional[int] = Field(default=None, alias='variationId')
    code: Optional[str] = None
    barcode: Optional[str] = None
    attributes: List[Attribute] = []
    tags: Optional[List[str]] = []
    buying_price: Optional[float] = Field(0, alias='buyingPrice')
    dimensions: Optional[Dimensions] = Field(default_factory=Dimensions)
    brand: Optional[str] = ''
    notes: Optional[str] = ''
    deals: Optional[List[Deal]] = []
    stocks: List[Stock]
    prices: Optional[List[Price]] = []
    pictures: Optional[List[Picture]] = []


class ProductVariation(ProductVariationBase):
    category: Optional[str] = Field(default=None)
    name: str


class Shipping(BaseModel):
    local_pickup: Optional[bool] = Field(default=None, alias='localPickup')
    mode: Optional[str] = None
    free_shipping: Optional[bool] = Field(default=None, alias='freeShipping')
    free_shipping_cost: Optional[float] = Field(default=None, alias='freeShippingCost')
    mandatory_free_shipping: Optional[bool] = Field(default=None, alias='mandatoryFreeShipping')
    free_shipping_method: Optional[str] = Field(default=None, alias='freeShippingMethod')


class MShopsShipping(BaseModel):
    enabled: Optional[bool] = None


class AttributeCompletion(BaseModel):
    product_identifier_status: Optional[str] = Field(default=None, alias='productIdentifierStatus')
    data_sheet_status: Optional[str] = Field(default=None, alias='dataSheetStatus')
    status: Optional[str] = None
    count: Optional[int] = None
    total: Optional[int] = None


class MeliProduct(BaseModel):
    product_id: Optional[int] = Field(default=None, alias='productId')
    tags: Optional[List[str]] = Field(default=None)
    has_custom_shipping_costs: Optional[bool] = Field(default=None, alias='hasCustomShippingCosts')
    shipping: Optional[Shipping] = None
    mshops_shipping: Optional[MShopsShipping] = Field(default=None, alias='mShopsShipping')
    add_free_shipping_cost_to_price: Optional[bool] = Field(default=None, alias='addFreeShippingCostToPrice')
    category: MeliCategory
    attribute_completion: Optional[AttributeCompletion] = Field(default=None, alias='attributeCompletion')
    catalog_products: Optional[List[str]] = Field(default=None, alias='catalogProducts')
    warranty: Optional[str] = None
    domain: Optional[str] = None
    listing_type_id: Optional[str] = Field(default=None, alias='listingTypeId')
    catalog_products_status: Optional[str] = Field(default=None, alias='catalogProductsStatus')


class ErrorMessage(BaseModel):
    en: str
    es: str
    pt: str


class ErrorReason(BaseModel):
    code: str
    error: str
    message: ErrorMessage
    data: Optional[dict] = None


class ResolvedValue(BaseModel):
    updated: bool


class ResolvedError(BaseModel):
    resolved: Optional[bool] = None
    reason: Optional[ErrorReason] = None
    value: Optional[ResolvedValue] = None
    statusCode: Optional[int] = None


class ErrorContext(BaseModel):
    _ns_name: str
    id: int
    requestId: str
    tokenAppId: str
    appId: str
    bearer: str
    eventId: str


class SynchronizeResponse(BaseModel):
    product: Optional[ResolvedError] = None
    variation: Optional[ResolvedError] = None
    deals: Optional[ResolvedError] = None
    bundles: Optional[ResolvedError] = None
    taxes: Optional[ResolvedError] = None
    meliProductListingIntegrations: Optional[ResolvedError] = None
    tags: Optional[ResolvedError] = None
    productIntegrations: Optional[ResolvedError] = None
    statusCode: Optional[int] = None
    error_context: Optional[ErrorContext] = Field(None, alias='error@context')


class ListedSynchronizeResponse(BaseModel):
    results: List[SynchronizeResponse]


@dataclass
class ProductService(BaseService):
    endpoint: str = 'products'
    create_if_it_doesnt_exist: bool = Field(default=False, exclude=True)

    def __call__(self, **payload):
        self._record = Product(**payload)
        return self

    def synchronize(self, payload) -> Union[Product, SynchronizeResponse]:

        endpoint_url = self.config.get_endpoint(f'{self.endpoint}/synchronize')
        headers = self.config.headers.copy()
        headers.update({"createifitdoesntexist": str(self.create_if_it_doesnt_exist).lower()})
        product_variation = ProductVariation(**payload)
        if not product_variation.code and not product_variation.sku:
            raise Exception("Sku or code should be provided to update the product")
        data = product_variation.model_dump(by_alias=True, exclude_none=True)
        response = requests.post(endpoint_url, json=data, headers=headers)
        response_data = response.json()
        try:
            return Product(**response_data)
        except ValidationError:
            pass
        if isinstance(response_data, list):
            res = ListedSynchronizeResponse(results=response_data)
            if any([r.error_context for r in res.results]):
                raise Exception(f"Errored while updating {res.results[0].error_context} {res.model_dump_json()}")
            else:
                return res.results[0]
        else:
            try:
                sync_resp = SynchronizeResponse(**response_data)
                if sync_resp.error_context:
                    raise Exception(f"Errored while updating {sync_resp.error_context} - {sync_resp.model_dump_json()}")
                else:
                    return sync_resp
            except ValidationError:
                try:
                    error_res = ErrorReason(**response_data)
                    raise Exception(f"Errored with the following message {error_res.message} - {error_res.model_dump_json()}")
                except ValidationError:
                    pass

        if not response.ok:
            raise Exception(f"Error getting product {product_variation.sku} - {product_variation.code}\n {response.text}")
        if response.status_code == 204:
            raise Exception("Status code is 204, meaning nothing was updated or created")
        raise Exception(f"Unhandled error, check response {response.text}")

    def get(self, product_id: int) -> "ProductService":
        endpoint_url = self.config.get_endpoint(f'{self.endpoint}/{product_id}')
        headers = self.config.headers
        response = requests.get(endpoint_url, headers=headers)
        if not response.ok:
            raise Exception(f"Error getting product {product_id}\n {response.text}")
        response_data = response.json()
        return self(**response_data)

    def get_bundle(self, product_id: int) -> BundleResponse:
        endpoint_url = self.config.get_endpoint(f'{self.endpoint}/{product_id}/bundles')
        headers = self.config.headers
        response = requests.get(endpoint_url, headers=headers)
        if not response.ok:
            raise Exception(f"Error getting bundle {product_id}\n {response.text}")
        return BundleResponse(**response.json())

    def get_ml_integration(self, product_id: int) -> MeliProduct:
        endpoint_url = self.config.get_endpoint(f'{self.endpoint}/{product_id}/listingintegration')
        headers = self.config.headers
        response = requests.get(endpoint_url, headers=headers)
        if not response.ok:
            raise Exception(f"Error getting ml integration {product_id}\n {response.text}")
        response_data = response.json()
        return MeliProduct(**response_data)

    def search(self, params: SearchProductParams) -> SearchProduct:
        endpoint: str = f'search/{self.endpoint}'
        headers = self.config.headers
        url = self.config.get_endpoint(endpoint)
        response = requests.get(url, headers=headers, params=params.model_dump(by_alias=True, exclude_none=True))
        if not response.ok:
            raise Exception(f"error in searching products {response.text}")
        return SearchProduct(**response.json())
