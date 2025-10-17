from dataclasses import dataclass, asdict
from typing import Optional
from fmconsult.utils.object import CustomObject

@dataclass
class Customer(CustomObject):
    email: str
    name: str
    cpf_cnpj: Optional[str] = None
    phone: Optional[int] = None
    phone_prefix: Optional[int] = None
    zip_code: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    complement: Optional[str] = None

    def to_dict(self):
        data = asdict(self)
        return data