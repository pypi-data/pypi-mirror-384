from dataclasses import dataclass
from fmconsult.utils.object import CustomObject

@dataclass
class KeyValue(CustomObject):
    name: str
    value: str