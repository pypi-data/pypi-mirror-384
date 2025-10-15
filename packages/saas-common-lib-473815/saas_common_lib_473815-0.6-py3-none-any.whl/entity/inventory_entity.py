from sqlalchemy import Column, Integer, BigInteger, Boolean, Text, DateTime, Float, func, ARRAY
from database.base import Base
from models.inventory_model import Inventory, Category
from sqlalchemy.dialects.postgresql import JSONB


class InventoryEntity(Base):
    __tablename__ = "inventory"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    client_id = Column(Text, nullable=False)
    inventory_id = Column(BigInteger, nullable=True)
    line_item_id = Column(ARRAY(BigInteger), nullable=True)
    name = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    category_id = Column(Text, nullable=True)
    realm = Column(Text, nullable=True)
    availability = Column(Integer, nullable=True)
    unit = Column(Text, nullable=True)
    unit_price = Column(Float, nullable=True)
    unit_cst = Column(Float, nullable=True)
    unit_gst = Column(Float, nullable=True)
    unit_total_price = Column(Float, nullable=True)
    price = Column(Float, nullable=True)
    cst = Column(Float, nullable=True)
    gst = Column(Float, nullable=True)
    discount = Column(Float, nullable=True)
    total_price = Column(Float, nullable=True)
    slug = Column(Text, nullable=True)
    created_by = Column(Text, nullable=True)
    updated_by = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    @staticmethod
    def copyToModel(row):
        model = Inventory(**row.__dict__)
        model.__dict__.pop("_sa_instance_state", None)
        return model

    @staticmethod
    def copyToModels(rows):
        models = [Inventory(**row.__dict__) for row in rows]
        for m in models:
            m.__dict__.pop("_sa_instance_state", None)
        return models


class CategoryEntity(Base):
    __tablename__ = "category"

    id = Column(Text, primary_key=True)
    client_id = Column(Text, nullable=False)
    name = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    sub_categories = Column(ARRAY(Text), nullable=True)
    # sub_categories  = Column(JSONB, nullable=True, default=[])
    slug = Column(Text, nullable=True)
    created_by = Column(Text, nullable=True)
    updated_by = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    @staticmethod
    def copyToModel(row):
        model = Category(**row.__dict__)
        model.__dict__.pop("_sa_instance_state", None)
        return model

    @staticmethod
    def copyToModels(rows):
        models = [Category(**row.__dict__) for row in rows]
        for m in models:
            m.__dict__.pop("_sa_instance_state", None)
        return models
