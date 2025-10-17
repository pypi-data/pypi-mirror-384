from dataclasses import dataclass, asdict
from typing import Optional
from fmconsult.utils.enum import CustomEnum
from fmconsult.utils.object import CustomObject
from iugu.dtos.keyvalue import KeyValue
from iugu.dtos.split import Split

@dataclass
class Item(CustomObject):
    description: str
    quantity: Optional[int] = None
    price_cents: Optional[float] = None

@dataclass
class Address(CustomObject):
    zip_code: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    complement: Optional[str] = None

@dataclass
class Payer(CustomObject):
    cpf_cnpj: str
    name: str
    email: Optional[str] = None
    phone_prefix: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Address] = None

@dataclass
class Invoice(CustomObject):
    email: str
    items: list[Item]
    due_date: str
    ensure_workday_due_date: Optional[bool] = None
    expires_in: Optional[str] = None
    payable_with: Optional[list[str]] = None
    payer: Optional[Payer] = None
    splits: Optional[list[Split]] = None
    customer_id: Optional[str] = None
    subscription_id: Optional[str] = None
    return_url: Optional[str] = None
    expired_url: Optional[str] = None
    notification_url: Optional[str] = None
    custom_variables: Optional[list[KeyValue]] = None
    order_id: Optional[str] = None
    external_reference: Optional[str] = None
    max_installments_value: Optional[int] = None
    pix_qr_code_expires_at: Optional[str] = None
    password: Optional[str] = None

    def to_dict(self):
        data = asdict(self)
        return data