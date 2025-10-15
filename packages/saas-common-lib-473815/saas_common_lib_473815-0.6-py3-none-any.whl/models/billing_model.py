from typing import Optional,List,Dict,Any
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class PaymentStatusEnum(str, Enum):
    pending  = "Pending"
    paid     = "Paid"
    partial  = "Partial"
    overdue  = "Overdue"

class ApprovalStatusEnum(str, Enum):
    pending  = "Pending"
    approved = "Approved"
    rejected = "Rejected"

class BillingDocument(BaseModel):
    id:                       Optional[int]      = None
    client_id:                Optional[str]      = None
    document_type:            Optional[str]      = None
    document_number:          Optional[str]      = None
    document_date:            Optional[datetime] = None
    due_date:                 Optional[datetime] = None
    reference_number:         Optional[str]      = None
    order_id:                 Optional[str]      = None
    customer_id:              Optional[str]      = None
    vendor_id:                Optional[str]      = None
    currency:                 Optional[str]      = "INR"
    status:                   Optional[str]      = "Draft"
    contact_email:            Optional[str]      = None
    contact_phone:            Optional[str]      = None
    terms:                    Optional[str]      = None
    notes:                    Optional[str]      = None
    subtotal:                 Optional[float]    = 0.0
    tax_amount:               Optional[float]    = 0.0
    discount_amount:          Optional[float]    = 0.0
    total_amount:             Optional[float]    = 0.0
    linked_document_ids:      Optional[str]      = None
    is_active:                Optional[bool]     = True
    created_by:               Optional[str]      = None
    updated_by:               Optional[str]      = None
    created_at:               Optional[datetime] = None
    updated_at:               Optional[datetime] = None
    payment_status:           Optional[PaymentStatusEnum] = PaymentStatusEnum.pending
    payment_due_date:         Optional[datetime] = None
    payment_method:           Optional[List[Dict[str, Any]]] = None
    payment_reference:        Optional[str]      = None
    approval_status:          Optional[ApprovalStatusEnum] = ApprovalStatusEnum.pending
    approved_by:              Optional[str]      = None
    approval_date:            Optional[datetime] = None
    gl_account_code:          Optional[str]      = None
    tax_code:                 Optional[str]      = None
    accounting_period:        Optional[str]      = None
    currency_conversion_rate: Optional[float]    = None
    shipping_address:         Optional[str]      = None
    shipping_method:          Optional[str]      = None
    delivery_date:            Optional[datetime] = None
    tracking_number:          Optional[str]      = None
    document_version:         Optional[int]      = 1
    invoice_date:             Optional[datetime] = None
    note:                     Optional[str]      = None
    customer_terms:           Optional[str]      = None

    class Config:
        orm_mode = True

class BillingDocumentItem(BaseModel):
    id:              Optional[int]       = None
    document_id:     Optional[int]       = None
    item_ref_id:     Optional[str]       = None
    description:     Optional[str]       = None
    quantity:        Optional[float]     = 0.0
    unit_price:      Optional[float]     = 0.0
    discount:        Optional[float]     = 0.0
    tax_rate:        Optional[float]     = 0.0
    total:           Optional[float]     = 0.0
    is_active:       Optional[bool]      = True
    created_at:      Optional[datetime]  = None
    updated_at:      Optional[datetime]  = None
    unit_of_measure: Optional[str]       = "Unit"
    item_category:   Optional[str]       = None
    item_discount:   Optional[float]     = 0.0
    item_tax_code:   Optional[str]       = "Standard"

    class Config:
        orm_mode = True
