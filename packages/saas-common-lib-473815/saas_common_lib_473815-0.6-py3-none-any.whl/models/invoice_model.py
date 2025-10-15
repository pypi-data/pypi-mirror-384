from pydantic import BaseModel
from typing import Optional

class InvoiceModel(BaseModel):
    id: Optional[int] = None
    clientId: Optional[str] = None
    invoiceId: Optional[str] = None
    orderId: Optional[str] = None
    orderItemId: Optional[str] = None
    itemDescription: Optional[str] = None
    quantity: Optional[int] = None
    price: Optional[float] = None
    cst: Optional[float] = None
    gst: Optional[float] = None