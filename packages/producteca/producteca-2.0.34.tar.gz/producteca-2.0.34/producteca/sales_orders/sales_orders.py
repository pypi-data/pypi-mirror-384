from pydantic import BaseModel, Field
from typing import List, Optional
import requests
from producteca.abstract.abstract_dataclass import BaseService
from producteca.sales_orders.search_sale_orders import SearchSalesOrderParams, SearchSalesOrder
from producteca.payments.payments import Payment
from producteca.shipments.shipment import Shipment
from dataclasses import dataclass
import logging
_logger = logging.getLogger(__name__)


class SaleOrderLocation(BaseModel):
    street_name: Optional[str] = Field(None, alias="streetName")
    street_number: Optional[str] = Field(None, alias="streetNumber") 
    address_notes: Optional[str] = Field(None, alias="addressNotes")
    state: Optional[str] = None
    city: Optional[str] = None
    neighborhood: Optional[str] = None
    zip_code: Optional[str] = Field(None, alias="zipCode")


class SaleOrderBillingInfo(BaseModel):
    doc_type: Optional[str] = Field(None, alias="docType")
    doc_number: Optional[str] = Field(None, alias="docNumber")
    street_name: Optional[str] = Field(None, alias="streetName")
    street_number: Optional[str] = Field(None, alias="streetNumber")
    comment: Optional[str] = None
    zip_code: Optional[str] = Field(None, alias="zipCode")
    city: Optional[str] = None
    state: Optional[str] = None
    state_registration: Optional[str] = Field(None, alias="stateRegistration")
    tax_payer_type: Optional[str] = Field(None, alias="taxPayerType")
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")
    business_name: Optional[str] = Field(None, alias="businessName")


class SaleOrderProfile(BaseModel):
    app: int
    integration_id: str = Field(alias="integrationId")
    nickname: Optional[str] = None


class SaleOrderContact(BaseModel):
    id: int
    name: str
    contact_person: Optional[str] = Field(None, alias="contactPerson")
    mail: Optional[str] = None
    phone_number: Optional[str] = Field(None, alias="phoneNumber")
    tax_id: Optional[str] = Field(None, alias="taxId")
    location: Optional[SaleOrderLocation] = None
    notes: Optional[str] = None
    type: Optional[str] = None
    price_list: Optional[str] = Field(None, alias="priceList")
    price_list_id: Optional[str] = Field(None, alias="priceListId")
    profile: Optional[SaleOrderProfile] = None
    billing_info: Optional[SaleOrderBillingInfo] = Field(None, alias="billingInfo")


class SaleOrderIntegrationId(BaseModel):
    alternate_id: Optional[str] = Field(None, alias="alternateId")
    integration_id: str = Field(alias="integrationId")
    app: int


class SaleOrderVariationPicture(BaseModel):
    url: str
    id: Optional[int] = None


class SaleOrderVariationStock(BaseModel):
    warehouse_id: Optional[int] = Field(None, alias="warehouseId")
    warehouse: str
    quantity: int
    reserved: int
    last_modified: Optional[str] = Field(None, alias="lastModified")
    available: int


class SaleOrderVariationAttribute(BaseModel):
    key: str
    value: str


class SaleOrderVariation(BaseModel):
    supplier_code: Optional[str] = Field(None, alias="supplierCode")
    pictures: Optional[List[SaleOrderVariationPicture]] = None
    stocks: Optional[List[SaleOrderVariationStock]] = None
    integration_id: Optional[int] = Field(None, alias="integrationId")
    attributes_hash: Optional[str] = Field(None, alias="attributesHash")
    primary_color: Optional[str] = Field(None, alias="primaryColor")
    secondary_color: Optional[str] = Field(None, alias="secondaryColor")
    size: Optional[str] = None
    thumbnail: Optional[str] = None
    attributes: Optional[List[SaleOrderVariationAttribute]] = None
    integrations: Optional[List[SaleOrderIntegrationId]] = None
    id: int
    sku: str
    barcode: Optional[str] = None


class SaleOrderProduct(BaseModel):
    name: str
    code: str
    brand: Optional[str] = None
    id: int


class SaleOrderQuestion(BaseModel):
    text: Optional[str] = None
    answer: Optional[str] = None


class SaleOrderConversation(BaseModel):
    questions: Optional[List[SaleOrderQuestion]] = None


class SaleOrderLine(BaseModel):
    price: float
    original_price: Optional[float] = Field(None, alias="originalPrice")
    transaction_fee: Optional[float] = Field(None, alias="transactionFee")
    product: SaleOrderProduct
    variation: SaleOrderVariation
    order_variation_integration_id: Optional[str] = Field(None, alias="orderVariationIntegrationId")
    quantity: int
    conversation: Optional[SaleOrderConversation] = None
    reserved: Optional[int] = None
    id: int


class SaleOrderCard(BaseModel):
    payment_network: Optional[str] = Field(None, alias="paymentNetwork")
    first_six_digits: Optional[int] = Field(None, alias="firstSixDigits")
    last_four_digits: Optional[int] = Field(None, alias="lastFourDigits")
    cardholder_identification_number: Optional[str] = Field(None, alias="cardholderIdentificationNumber")
    cardholder_identification_type: Optional[str] = Field(None, alias="cardholderIdentificationType")
    cardholder_name: Optional[str] = Field(None, alias="cardholderName")


class SaleOrderPaymentIntegration(BaseModel):
    integration_id: str = Field(alias="integrationId")
    app: int


class SaleOrderPayment(BaseModel):
    date: Optional[str] = None
    amount: float
    coupon_amount: Optional[float] = Field(None, alias="couponAmount")
    status: Optional[str] = None
    method: Optional[str] = None
    integration: Optional[SaleOrderPaymentIntegration] = None
    transaction_fee: Optional[float] = Field(None, alias="transactionFee")
    installments: Optional[int] = None
    card: Optional[SaleOrderCard] = None
    notes: Optional[str] = None
    authorization_code: Optional[str] = Field(None, alias="authorizationCode")
    has_cancelable_status: Optional[bool] = Field(None, alias="hasCancelableStatus")
    id: Optional[int] = None


class SaleOrderShipmentMethod(BaseModel):
    tracking_number: Optional[str] = Field(None, alias="trackingNumber")
    tracking_url: Optional[str] = Field(None, alias="trackingUrl")
    courier: Optional[str] = None
    mode: Optional[str] = None
    cost: Optional[float] = None
    type: Optional[str] = None
    eta: Optional[int] = None
    status: Optional[str] = None


class SaleOrderShipmentProduct(BaseModel):
    product: int
    variation: int
    quantity: int


class SaleOrderShipmentIntegration(BaseModel):
    app: int
    integration_id: str = Field(alias="integrationId")
    status: str
    id: int


class SaleOrderShipment(BaseModel):
    date: str
    products: List[SaleOrderShipmentProduct]
    method: Optional[SaleOrderShipmentMethod] = None
    integration: Optional[SaleOrderShipmentIntegration] = None
    receiver: Optional[dict] = None
    id: int


class SaleOrderInvoiceIntegrationAbstract(BaseModel):
    id: int
    integration_id: str = Field(alias="integrationId")
    app: int
    created_at: str = Field(alias="createdAt")
    decrease_stock: Optional[bool] = Field(None, alias="decreaseStock")


class SaleOrderInvoiceIntegration(SaleOrderInvoiceIntegrationAbstract):
    document_url: Optional[str] = Field(None, alias="documentUrl")
    xml_url: Optional[str] = Field(None, alias="xmlUrl")


class SaleOrderInvoiceIntegrationPut(SaleOrderInvoiceIntegrationAbstract):
    document_url: Optional[str] = Field(None, alias="documentUrl")
    xml_url: Optional[str] = Field(None, alias="xmlUrl")

class SaleOrderWarehouseIntegration(BaseModel):
    app: Optional[int] = None
    status: Optional[str] = None
    integration_id: Optional[str] = Field(None, alias="integrationId")


class SaleOrder(BaseModel):
    tags: Optional[List[str]] = None
    integrations: Optional[List[SaleOrderIntegrationId]] = None
    invoice_integration: Optional[SaleOrderInvoiceIntegration] = Field(None, alias="invoiceIntegration")
    channel: Optional[str] = None
    pii_expired: Optional[bool] = Field(None, alias="piiExpired")
    contact: Optional[SaleOrderContact] = None
    lines: Optional[List[SaleOrderLine]] = None
    warehouse: Optional[str] = None
    warehouse_id: Optional[int] = Field(None, alias="warehouseId")
    warehouse_integration: Optional[SaleOrderWarehouseIntegration] = Field(None, alias="warehouseIntegration")
    pick_up_store: Optional[str] = Field(None, alias="pickUpStore")
    payments: Optional[List[SaleOrderPayment]] = None
    shipments: Optional[List[SaleOrderShipment]] = None
    amount: Optional[float] = None
    shipping_cost: Optional[float] = Field(None, alias="shippingCost")
    financial_cost: Optional[float] = Field(None, alias="financialCost")
    paid_approved: Optional[float] = Field(None, alias="paidApproved")
    payment_status: Optional[str] = Field(None, alias="paymentStatus")
    delivery_status: Optional[str] = Field(None, alias="deliveryStatus")
    payment_fulfillment_status: Optional[str] = Field(None, alias="paymentFulfillmentStatus")
    delivery_fulfillment_status: Optional[str] = Field(None, alias="deliveryFulfillmentStatus")
    delivery_method: Optional[str] = Field(None, alias="deliveryMethod")
    payment_term: Optional[str] = Field(None, alias="paymentTerm")
    currency: Optional[str] = None
    custom_id: Optional[str] = Field(None, alias="customId")
    is_open: Optional[bool] = Field(None, alias="isOpen")
    is_canceled: Optional[bool] = Field(None, alias="isCanceled")
    cart_id: Optional[str] = Field(None, alias="cartId")
    draft: Optional[bool] = None
    promise_delivery_date: Optional[str] = Field(None, alias="promiseDeliveryDate")
    promise_dispatch_date: Optional[str] = Field(None, alias="promiseDispatchDate")
    has_any_shipments: Optional[bool] = Field(None, alias="hasAnyShipments")
    has_any_payments: Optional[bool] = Field(None, alias="hasAnyPayments")
    date: Optional[str] = None
    notes: Optional[str] = None
    id: int


class SaleOrderSynchronize(BaseModel):
    id: int
    invoice_integration: SaleOrderInvoiceIntegration = Field(alias="invoiceIntegration")
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class UpdateStatus(BaseModel):
    updated: bool = False


class SaleOrderSyncResponse(BaseModel):
    basic: UpdateStatus = Field(default_factory=UpdateStatus)
    contact: UpdateStatus = Field(default_factory=UpdateStatus)
    shipments: UpdateStatus = Field(default_factory=UpdateStatus) 
    payments: UpdateStatus = Field(default_factory=UpdateStatus)
    invoice_integration: UpdateStatus = Field(alias="invoiceIntegration", default_factory=UpdateStatus)


@dataclass
class SaleOrderService(BaseService):
    endpoint: str = 'salesorders'

    def __call__(self, **payload):
        self._record = SaleOrder(**payload)
        return self

    def __repr__(self):
        return repr(self._record)
    
    def get(self, sale_order_id: int) -> "SaleOrderService":
        endpoint = f'{self.endpoint}/{sale_order_id}'
        url = self.config.get_endpoint(endpoint)
        response = requests.get(url, headers=self.config.headers)
        if not response.ok:
            raise Exception(f"Order {sale_order_id} could not be fetched")
        response_data = response.json()
        return self(**response_data)

    def get_shipping_labels(self):
        if not self._record:
            raise Exception("You need to add a record id")
        endpoint = f'{self.endpoint}/{self._record.id}/labels'
        url = self.config.get_endpoint(endpoint)
        response = requests.get(url, headers=self.config.headers)
        if not response.ok:
            raise Exception("labels could not be gotten")
        return response.json()

    def close(self):
        if not self._record:
            raise Exception("You need to add a record id")
        endpoint = f'{self.endpoint}/{self._record.id}/close'
        url = self.config.get_endpoint(endpoint)
        response = requests.post(url, headers=self.config.headers)
        if not response.ok:
            raise Exception("Order could not be closed")

    def cancel(self):
        if not self._record:
            raise Exception("You need to add a record id")
        endpoint = f'{self.endpoint}/{self._record.id}/cancel'
        url = self.config.get_endpoint(endpoint)
        response = requests.post(url, headers=self.config.headers)
        if not response.ok:
            raise Exception("Order could not be cancelled")

    def synchronize(self) -> "SaleOrderService":
        if not self._record:
            raise Exception("You need to add a record by calling the resource and adding info")
        endpoint = f'{self.endpoint}/synchronize'
        url = self.config.get_endpoint(endpoint)
        # TODO: Check what can we sync, and what can we not sync
        sync_body = SaleOrderSynchronize(**self._record.model_dump(by_alias=True))
        response = requests.post(url, json=sync_body.model_dump(by_alias=True), headers=self.config.headers)
        if not response.ok:
            raise Exception(f"Synchronize error {response.status_code} {response.text}")
        sync_res = SaleOrderSyncResponse(**response.json()) # noqa
        return self

    def invoice_integration(self):
        if not self._record:
            raise Exception("You need to add a record id")
        endpoint = f'{self.endpoint}/{self._record.id}/invoiceIntegration'
        url = self.config.get_endpoint(endpoint)
        response = requests.put(url, headers=self.config.headers,
                                json={"id": self._record.id,
                                      "invoiceIntegration": SaleOrderInvoiceIntegrationPut(**self._record.invoice_integration.model_dump(by_alias=True)).model_dump()})
        if not response.ok:
            raise Exception(f"Error on resposne {response.text}")
        return response.ok

    def search(self, params: SearchSalesOrderParams):
        endpoint: str = f"search/{self.endpoint}"
        headers = self.config.headers
        url = self.config.get_endpoint(endpoint)
        new_url = f"{url}?$filter={params.filter}&top={params.top}&skip={params.skip}"
        response = requests.get(
            new_url,
            headers=headers,
        )
        if not response.ok:
            raise Exception(f"Error on resposne {response.status_code} - {response.text}")
        response_data = response.json()
        return SearchSalesOrder(**response_data)

    def add_payment(self, payload) -> Payment:
        if not self._record:
            raise Exception("You need to add a record id")
        payment = Payment(**payload)
        url = self.config.get_endpoint(f"{self.endpoint}/{self._record.id}/payments")
        res = requests.post(url, json=payment.model_dump(by_alias=True, exclude_none=True), headers=self.config.headers)
        if not res.ok:
            raise Exception(f"Error on resposne {res.text}")
        return Payment(**res.json())

    def update_payment(self, payment_id: int, payload) -> "Payment":
        if not self._record:
            raise Exception("You need to add a record id")
        payment = Payment(**payload)
        url = self.config.get_endpoint(f"{self.endpoint}/{self._record.id}/payments/{payment_id}")
        res = requests.put(url, json=payment.model_dump(by_alias=True, exclude_none=True), headers=self.config.headers)
        if not res.ok:
            raise Exception(f"Error on payment update {res.text}")
        return Payment(**res.json())

    def add_shipment(self, payload) -> "Shipment":
        if not self._record:
            raise Exception("You need to add a record id")
        shipment = Shipment(**payload)
        url = self.config.get_endpoint(f"{self.endpoint}/{self._record.id}/shipments")
        res = requests.post(url, json=shipment.model_dump(by_alias=True, exclude_none=True), headers=self.config.headers)
        if not res.ok:
            raise Exception(f"Error on shipment add {res.text}")
        return Shipment(**res.json())

    def update_shipment(self, shipment_id: str, payload) -> "Shipment":
        if not self._record:
            raise Exception("You need to add a record id")
        shipment = Shipment(**payload)
        url = self.config.get_endpoint(f"{self.endpoint}/{self._record.id}/shipments/{shipment_id}")
        res = requests.put(url, json=shipment.model_dump(by_alias=True, exclude_none=True), headers=self.config.headers)
        if not res.ok:
            raise Exception(f"Error on shipment update {res.text}")
        return Shipment(**res.json())
