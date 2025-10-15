from sqlalchemy import Column, Integer, BigInteger, Boolean, Text, DateTime, func, UniqueConstraint, Identity
from sqlalchemy.dialects.postgresql import UUID
import uuid
from database.base import Base
from models.table_model import Table


class DiningTable(Base):
    __tablename__ = "tables"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    client_id = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    table_type = Column(Text)
    slug = Column(Text, unique=True, nullable=True)
    qr_code_url = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(Text, nullable=True, default="Vacant")
    section = Column(Text, nullable=True)
    location_zone = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(Text, nullable=True)
    updated_by = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


    @staticmethod
    def copyToModel(table):
        model = Table(**table.__dict__)
        model.__dict__.pop("_sa_instance_state", None)
        return model

    @staticmethod
    def copyToModels(tables):
        models = [Table(**table.__dict__) for table in tables]
        for m in models:
            m.__dict__.pop("_sa_instance_state", None)
        return models
