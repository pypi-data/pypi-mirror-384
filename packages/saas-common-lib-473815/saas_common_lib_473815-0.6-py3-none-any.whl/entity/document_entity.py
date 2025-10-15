from sqlalchemy import Column, Boolean, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from database.base import Base
from models.document_model import Document

class DocumentEntity(Base):
    __tablename__ = "documents"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id           = Column(Text, nullable=True)
    category_id         = Column(Text, nullable=True)
    name                = Column(Text, nullable=True)
    description         = Column(Text, nullable=True)
    realm               = Column(Text, nullable=True)
    filetype            = Column(Text, nullable=True)
    extension           = Column(Text, nullable=True)
    size_kb             = Column(Text, nullable=True)
    is_protected        = Column(Boolean, nullable=True)
    is_active           = Column(Boolean, nullable=True)
    uuid_name           = Column(Text, nullable=True)
    path                = Column(Text, nullable=True)
    storage_type        = Column(Text, nullable=True)
    checksum_md5        = Column(Text, nullable=True)
    created_by          = Column(Text, nullable=True)
    last_read_by        = Column(Text, nullable=True)
    created_date_time   = Column(DateTime, default=func.now())
    last_read_date_time = Column(DateTime, default=func.now())

    deleted             = Column(Boolean, nullable=True)
    deleted_at          = Column(DateTime, nullable=True)

    @staticmethod
    def copyToModel(document):
        model = Document(**document.__dict__)
        model.__dict__.pop("_sa_instance_state", None)
        return model

    @staticmethod
    def copyToModels(docs):
        models = [Document(**doc.__dict__) for doc in docs]
        for m in models:
            m.__dict__.pop("_sa_instance_state", None)
        return models
