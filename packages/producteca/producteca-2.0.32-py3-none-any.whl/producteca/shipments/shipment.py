from typing import List, Optional
from pydantic import BaseModel


class ShipmentProduct(BaseModel):
    product: int
    variation: Optional[int] = None
    quantity: int


class ShipmentMethod(BaseModel):
    trackingNumber: Optional[str] = None
    trackingUrl: Optional[str] = None
    courier: Optional[str] = None
    mode: Optional[str] = None
    cost: Optional[float] = None
    type: Optional[str] = None
    eta: Optional[int] = None
    status: Optional[str] = None


class ShipmentIntegration(BaseModel):
    id: Optional[int] = None
    integrationId: Optional[str] = None
    app: Optional[int] = None
    status: str


class Shipment(BaseModel):
    date: Optional[str] = None
    products: Optional[List[ShipmentProduct]] = None
    method: Optional[ShipmentMethod] = None
    integration: Optional[ShipmentIntegration] = None
