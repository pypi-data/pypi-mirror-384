from sqlalchemy import Column, BigInteger, Text, Float, DateTime, Boolean, Identity, ForeignKey, func, Integer
from sqlalchemy.dialects.postgresql import JSONB
from database.base import Base
from models.billing_model import BillingDocument, BillingDocumentItem
from enum import Enum

class PaymentStatusEnum(str, Enum):
    pending = "Pending"
    paid    = "Paid"
    partial = "Partial"
    overdue = "Overdue"

class ApprovalStatusEnum(str, Enum):
    pending  = "Pending"
    approved = "Approved"
    rejected = "Rejected"

class BillingDocumentEntity(Base):
    __tablename__ = "billing_documents"

    id                       = Column(BigInteger, Identity(always=True), primary_key=True)
    client_id                = Column(Text, nullable=True)
    document_type            = Column(Text, nullable=True) # Quotation, 
    document_number          = Column(Text, nullable=True)
    document_date            = Column(DateTime, nullable=True)
    due_date                 = Column(DateTime, nullable=True)
    reference_number         = Column(Text, nullable=True)
    order_id                 = Column(Text, nullable=True)
    customer_id              = Column(Text, nullable=True)
    vendor_id                = Column(Text, nullable=True)
    currency                 = Column(Text, nullable=True)
    status                   = Column(Text, nullable=True) # paid, cancelled, partially paid
    contact_email            = Column(Text, nullable=True)
    contact_phone            = Column(Text, nullable=True)
    terms                    = Column(Text, nullable=True)
    notes                    = Column(Text, nullable=True)
    subtotal                 = Column(Float, nullable=True)
    tax_amount               = Column(Float, nullable=True) #
    discount_amount          = Column(Float, nullable=True)
    total_amount             = Column(Float, nullable=True)
    linked_document_ids      = Column(Text, nullable=True)
    is_active                = Column(Boolean, nullable=False, default=True)
    created_by               = Column(Text, nullable=True)
    updated_by               = Column(Text, nullable=True)
    created_at               = Column(DateTime, default=func.now())
    updated_at               = Column(DateTime, default=func.now(), onupdate=func.now())
    payment_status           = Column(Text, nullable=True, default=PaymentStatusEnum.pending)
    payment_due_date         = Column(DateTime, nullable=True)
    payment_method           = Column(JSONB, nullable=True)
    payment_reference        = Column(Text, nullable=True)
    approval_status          = Column(Text, nullable=True, default=ApprovalStatusEnum.pending) # rejected
    approved_by              = Column(Text, nullable=True)
    approval_date            = Column(DateTime, nullable=True)
    gl_account_code          = Column(Text, nullable=True)
    tax_code                 = Column(Text, nullable=True)
    accounting_period        = Column(Text, nullable=True)
    currency_conversion_rate = Column(Float, nullable=True)
    shipping_address         = Column(Text, nullable=True)
    shipping_method          = Column(Text, nullable=True)
    delivery_date            = Column(DateTime, nullable=True)
    tracking_number          = Column(Text, nullable=True)
    document_version         = Column(Integer, default=1)
    invoice_date             = Column(DateTime, nullable=True)
    note                     = Column(Text, nullable=True)
    customer_terms           = Column(Text, nullable=True)

    @staticmethod
    def copyToModel(entity):
        model = BillingDocument(**entity.__dict__)
        model.__dict__.pop("_sa_instance_state", None)
        return model

    @staticmethod
    def copyToModels(entities):
        models = [BillingDocument(**e.__dict__) for e in entities]
        for m in models:
            m.__dict__.pop("_sa_instance_state", None)
        return models

class BillingDocumentItemEntity(Base):
    __tablename__   = "billing_document_items"

    id              = Column(BigInteger, Identity(always=True), primary_key=True)
    document_id     = Column(BigInteger, ForeignKey("billing_documents.id", ondelete="CASCADE"), nullable=True) 
    item_ref_id     = Column(Text, nullable=True)
    description     = Column(Text, nullable=True)
    quantity        = Column(Float, nullable=True)
    unit_price      = Column(Float, nullable=True)
    discount        = Column(Float, nullable=True)
    tax_rate        = Column(Float, nullable=True)
    total           = Column(Float, nullable=True)
    is_active       = Column(Boolean, nullable=False, default=True)
    created_at      = Column(DateTime, default=func.now())
    updated_at      = Column(DateTime, default=func.now(), onupdate=func.now())
    unit_of_measure = Column(Text, nullable=True, default="Unit")
    item_category   = Column(Text, nullable=True)
    item_discount   = Column(Float, nullable=True, default=0.0)
    item_tax_code   = Column(Text, nullable=True, default="Standard")

    @staticmethod
    def copyToModel(entity):
        model = BillingDocumentItem(**entity.__dict__)
        model.__dict__.pop("_sa_instance_state", None)
        return model

    @staticmethod
    def copyToModels(entities):
        models = [BillingDocumentItem(**e.__dict__) for e in entities]
        for m in models:
            m.__dict__.pop("_sa_instance_state", None)
        return models



             



