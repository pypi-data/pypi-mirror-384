from dataclasses import dataclass, asdict
from typing import Optional
from fmconsult.utils.object import CustomObject
from iugu.dtos.split import Split
from iugu.dtos.keyvalue import KeyValue

@dataclass
class Subscription(CustomObject):
    customer_id: str
    plan_identifier: Optional[str] = None
    expires_at: Optional[str] = None
    splits: Optional[list[Split]] = None
    only_on_charge_success: Optional[bool] = None
    ignore_due_email: Optional[bool] = None
    payable_with: Optional[list[str]] = None
    credits_based: Optional[bool] = None
    price_cents: Optional[int] = None
    credits_cycle: Optional[int] = None
    credits_min: Optional[int] = None
    custom_variables: Optional[list[KeyValue]] = None
    two_step: Optional[bool] = None
    suspend_on_invoice_expired: Optional[bool] = None
    only_charge_on_due_date: Optional[bool] = None
    soft_descriptor_light: Optional[str] = None
    return_url: Optional[str] = None

    def to_dict(self):
        data = asdict(self)
        return data