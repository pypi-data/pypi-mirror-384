from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, ARRAY,BigInteger
from sqlalchemy.orm import declarative_base, relationship
import datetime
from models.order_model import OrderItemModel, DineinOrderModel
Base = declarative_base()


# DineinOrders Table
class DineinOrder(Base):
    __tablename__ = "dinein_order"

    id = Column(Integer, primary_key=True)
    client_id = Column(String, nullable=True)
    dinein_order_id = Column(String, nullable=True)
    table_id = Column(Integer, nullable=True)
    invoice_id = Column(String, nullable=True)
    handler_id = Column(String, nullable=True)
    invoice_status = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    cst = Column(Float, nullable=True)
    gst = Column(Float, nullable=True)
    discount = Column(Float, nullable=True)
    total_price = Column(Float, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)
    status = Column(String, nullable=True)
    items = relationship("OrderItem", backref="order",
                         cascade="all, delete-orphan")

    @staticmethod
    def copyToModel(dineinOrder):
        """Convert SQLAlchemy DineinOrders entities into Pydantic models."""
        dineinOrderModel = DineinOrderModel(**dineinOrder.__dict__)
        dineinOrderModel.__dict__.pop("_sa_instance_state", None)
        return dineinOrderModel

    @staticmethod
    def copyFromModel(dineinOrderModel):
        """Convert Pydantic DineinOrders models into SQLAlchemy entities."""
        return DineinOrder(**dineinOrderModel.dict(exclude_unset=True))

    @staticmethod
    def copyToModels(dinein_orders):
        """Convert SQLAlchemy DineinOrders entities into Pydantic models."""
        dineinOrdersModels = [DineinOrderModel(
            **order.__dict__) for order in dinein_orders]

        # Remove SQLAlchemy metadata (_sa_instance_state)
        for model in dineinOrdersModels:
            model.__dict__.pop("_sa_instance_state", None)

        return dineinOrdersModels

    @staticmethod
    def copyFromModels(dinein_orders_models):
        """Convert Pydantic DineinOrders models into SQLAlchemy entities."""
        return [DineinOrder(**model.dict(exclude_unset=True)) for model in dinein_orders_models]


# OrderItems Table
class OrderItem(Base):
    __tablename__ = "order_item"

    id = Column(Integer, primary_key=True)
    client_id = Column(String, nullable=True)
    order_id = Column(Integer, ForeignKey("dinein_order.id"))
    item_id = Column(Integer, nullable=True)
    item_name = Column(String, nullable=True)
    slug = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    unit_price = Column(Float, nullable=True)   
    line_total = Column(Float, nullable=True)   
    status = Column(String, nullable=True)

    @staticmethod
    def copyToModel(orderItem):
        """Convert SQLAlchemy OrderItems entities into Pydantic models."""
        orderItemModel = OrderItemModel(**orderItem.__dict__)
        orderItemModel.__dict__.pop("_sa_instance_state", None)
        return orderItemModel

    @staticmethod
    def copyFromModel(orderItemModel):
        """Convert Pydantic OrderItems models into SQLAlchemy entities."""
        return OrderItem(**orderItemModel.dict(exclude_unset=True))

    @staticmethod
    def copyToModels(order_items):
        """Convert SQLAlchemy OrderItems entities into Pydantic models."""
        orderItemModels = [OrderItemModel(**item.__dict__)
                           for item in order_items]
        for model in orderItemModels:
            model.__dict__.pop("_sa_instance_state", None)
        return orderItemModels

    @staticmethod
    def copyFromModels(order_item_models):
        """Convert Pydantic OrderItems models into SQLAlchemy entities."""
        return [OrderItem(**model.dict(exclude_unset=True)) for model in order_item_models]
