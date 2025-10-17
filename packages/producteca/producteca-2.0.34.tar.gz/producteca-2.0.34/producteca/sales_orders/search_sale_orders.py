from typing import List, Optional, Union
from pydantic import BaseModel, Field
import logging

_logger = logging.getLogger(__name__)


class SalesOrderProduct(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    brand: Optional[str] = None


class SalesOrderVariationAttribute(BaseModel):
    key: Optional[str] = None
    value: Optional[str] = None


class SalesOrderVariation(BaseModel):
    id: int
    attributes: Optional[List[SalesOrderVariationAttribute]] = None
    sku: Optional[str] = None
    thumbnail: Optional[str] = None


class SalesOrderLine(BaseModel):
    product: SalesOrderProduct
    variation: Optional[SalesOrderVariation] = None
    quantity: int
    price: float


class SalesOrderCard(BaseModel):
    payment_network: str = Field(alias="paymentNetwork")
    first_six_digits: int = Field(alias="firstSixDigits")
    last_four_digits: int = Field(alias="lastFourDigits")
    cardholder_identification_number: str = Field(alias="cardholderIdentificationNumber")
    cardholder_identification_type: str = Field(alias="cardholderIdentificationType")
    cardholder_name: str = Field(alias="cardholderName")


class SalesOrderPaymentIntegration(BaseModel):
    integration_id: str = Field(alias="integrationId")
    app: int


class SalesOrderPayment(BaseModel):
    date: str
    amount: float
    coupon_amount: float = Field(alias="couponAmount")
    status: str
    method: str
    integration: Optional[SalesOrderPaymentIntegration] = None
    transaction_fee: float = Field(alias="transactionFee")
    installments: int
    card: Optional[SalesOrderCard] = None
    notes: Optional[str] = None
    has_cancelable_status: bool = Field(alias="hasCancelableStatus")
    id: int


class SalesOrderIntegration(BaseModel):
    alternate_id: Optional[str] = Field(default=None, alias="alternateId")
    integration_id: Union[str, int] = Field(alias="integrationId")
    app: int


class SalesOrderShipmentProduct(BaseModel):
    product: int
    variation: int
    quantity: int


class SalesOrderShipmentMethod(BaseModel):
    tracking_number: Optional[str] = Field(alias="trackingNumber")
    tracking_url: Optional[str] = Field(alias="trackingUrl")
    courier: Optional[str] = None
    mode: Optional[str] = None
    cost: Optional[float] = None
    type: Optional[str] = None
    eta: Optional[Union[int, str]] = Field(None)
    status: Optional[str] = None


class SalesOrderShipmentIntegration(BaseModel):
    id: int
    integration_id: str = Field(alias="integrationId")
    app: int
    status: str


class SalesOrderShipment(BaseModel):
    date: str
    products: List[SalesOrderShipmentProduct]
    method: SalesOrderShipmentMethod
    integration: Optional[SalesOrderShipmentIntegration] = None


class SalesOrderResultItem(BaseModel):
    codes: List[str]
    contact_id: Optional[int] = Field(default=None, alias="contactId")
    currency: str
    date: str
    delivery_method: str = Field(alias="deliveryMethod")
    delivery_status: str = Field(alias="deliveryStatus")
    id: str
    integration_ids: List[str] = Field(alias="integrationIds")
    integrations: List[SalesOrderIntegration]
    invoice_integration_app: Optional[int] = Field(default=None, alias="invoiceIntegrationApp")
    invoice_integration_id: Optional[str] = Field(default=None, alias="invoiceIntegrationId")
    lines: List[SalesOrderLine]
    payments: Optional[List[SalesOrderPayment]] = None
    payment_status: str = Field(alias="paymentStatus")
    payment_term: str = Field(alias="paymentTerm")
    product_names: List[str] = Field(alias="productNames")
    reserving_product_ids: Union[str, List[str]] = Field(alias="reservingProductIds")
    sales_channel: int = Field(alias="salesChannel")
    shipments: Optional[List[SalesOrderShipment]] = None
    tracking_number: Optional[str] = Field(alias="trackingNumber")
    skus: List[str]
    status: str
    tags: List[str]
    warehouse: str
    company_id: int = Field(alias="companyId")
    shipping_cost: float = Field(alias="shippingCost")
    contact_phone: Optional[str] = Field(default=None, alias="contactPhone")
    brands: List[str]
    courier: Optional[str] = None
    order_id: int = Field(alias="orderId")
    updated_at: str = Field(alias="updatedAt")
    invoice_integration_created_at: Optional[str] = Field(default=None, alias="invoiceIntegrationCreatedAt")
    invoice_integration_document_url: Optional[str] = Field(default=None, alias="invoiceIntegrationDocumentUrl")
    has_document_url: bool = Field(alias="hasDocumentUrl")
    integration_alternate_ids: Union[str, List[str]] = Field(alias="integrationAlternateIds")
    cart_id: Optional[str] = Field(default=None, alias="cartId")
    amount: float
    has_any_shipments: bool = Field(alias="hasAnyShipments")


class SearchSalesOrder(BaseModel):
    count: int
    results: List[SalesOrderResultItem]


class SearchSalesOrderParams(BaseModel):
    top: Optional[int]
    skip: Optional[int]
    filter: Optional[str] = Field(default=None, alias="$filter")

    class Config:
        validate_by_name = True
