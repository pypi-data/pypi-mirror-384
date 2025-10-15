from sqlalchemy import Column, Text, DateTime, func, ARRAY
from sqlalchemy.dialects.postgresql import UUID
import uuid
from database.base import Base
from models.client_model import ClientModel


class Client(Base):
    __tablename__ = "client"

    id = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    realm = Column(Text)
    email = Column(Text, unique=True, nullable=True)
    phone = Column(Text, nullable=True)
    logo = Column(Text, nullable=True)
    saved_address_ids = Column(ARRAY(Text), nullable=True)
    created_date_time = Column(DateTime, default=func.now())
    updated_date_time = Column(DateTime, default=func.now(), onupdate=func.now())


    @staticmethod
    def copyToModel(client):
        model = ClientModel(**client.__dict__)
        model.__dict__.pop("_sa_instance_state", None)
        return model

