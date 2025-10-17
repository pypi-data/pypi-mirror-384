from dataclasses import dataclass, asdict
from typing import Optional
from fmconsult.utils.enum import CustomEnum
from fmconsult.utils.object import CustomObject

class IntervalType(CustomEnum):
    MONTHS = "months"
    WEEKS = "weeks"

@dataclass
class Plan(CustomObject):
  name: str
  identifier: str
  interval: int
  interval_type: IntervalType
  value_cents: float
  payable_with: Optional[list[str]] = None
  billing_days: Optional[int] = None

  def to_dict(self):
    data = asdict(self)
    data['interval_type'] = data['interval_type'].value
    return data