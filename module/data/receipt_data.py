from dataclasses import dataclass
from typing import List


@dataclass
class ItemData:
    name: str
    quantity: int
    unit_price: int
    total_price: int

@dataclass
class ReceiptData:
    items: List[ItemData]
    subtotal: int
    tax: int
    service_charge: int
    others: int
    total: int


