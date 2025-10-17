from pydantic import BaseModel
from typing import Optional


class PaymentCard(BaseModel):
    paymentNetwork: Optional[str] = None
    firstSixDigits: Optional[int] = None
    lastFourDigits: Optional[int] = None
    cardholderIdentificationNumber: Optional[str] = None
    cardholderIdentificationType: Optional[str] = None
    cardholderName: Optional[str] = None


class PaymentIntegration(BaseModel):
    integrationId: str
    app: int


class Payment(BaseModel):
    date: str
    amount: float
    couponAmount: Optional[float] = None
    status: str
    method: str
    integration: Optional[PaymentIntegration] = None
    transactionFee: Optional[float] = None
    installments: Optional[int] = None
    card: Optional[PaymentCard] = None
    notes: Optional[str] = None
    hasCancelableStatus: bool
    id: Optional[int] = None


