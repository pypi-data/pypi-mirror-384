from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, ARRAY
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

# Invoice Table
class Invoice(Base):
    __tablename__ = "Invoice"

    id = Column(Integer, primary_key=True)
    clientId = Column(String, nullable=True)
    invoiceId = Column(String, nullable=True)
    orderId = Column(String, nullable=True)
    orderItemId = Column(String, nullable=True)
    itemDescription = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    price = Column(Float, nullable=True)
    cst = Column(Float, nullable=True)
    gst = Column(Float, nullable=True)