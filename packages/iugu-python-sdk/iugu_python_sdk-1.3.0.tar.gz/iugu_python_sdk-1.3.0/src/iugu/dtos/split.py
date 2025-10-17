from dataclasses import dataclass, asdict
from typing import Optional
from fmconsult.utils.object import CustomObject

@dataclass
class Split(CustomObject):
    recipient_account_id: str
    cents: Optional[int] = None
    percent: Optional[float] = None
    permit_aggregated: Optional[bool] = None
    bank_slip_cents: Optional[int] = None
    bank_slip_percent: Optional[float] = None
    credit_card_cents: Optional[int] = None
    credit_card_percent: Optional[float] = None
    pix_cents: Optional[int] = None
    pix_percent: Optional[float] = None
    credit_card_1x_cents: Optional[int] = None
    credit_card_2x_cents: Optional[int] = None
    credit_card_3x_cents: Optional[int] = None
    credit_card_4x_cents: Optional[int] = None
    credit_card_5x_cents: Optional[int] = None
    credit_card_6x_cents: Optional[int] = None
    credit_card_7x_cents: Optional[int] = None
    credit_card_8x_cents: Optional[int] = None
    credit_card_9x_cents: Optional[int] = None
    credit_card_10x_cents: Optional[int] = None
    credit_card_11x_cents: Optional[int] = None
    credit_card_12x_cents: Optional[int] = None
    credit_card_1x_percent: Optional[float] = None
    credit_card_2x_percent: Optional[float] = None
    credit_card_3x_percent: Optional[float] = None
    credit_card_4x_percent: Optional[float] = None
    credit_card_5x_percent: Optional[float] = None
    credit_card_6x_percent: Optional[float] = None
    credit_card_7x_percent: Optional[float] = None
    credit_card_8x_percent: Optional[float] = None
    credit_card_9x_percent: Optional[float] = None
    credit_card_10x_percent: Optional[float] = None
    credit_card_11x_percent: Optional[float] = None
    credit_card_12x_percent: Optional[float] = None