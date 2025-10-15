import uuid
from database.postgres import Base
from sqlalchemy import Column , Integer, String, ARRAY, UUID, event, Date,TIMESTAMP,func,DateTime
from models.user_model import UserModel, PageDefinitionModel,PersonModel



class Person(Base):
    __tablename__ = "person"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String, index=True, nullable=False)
    last_name = Column(String, nullable=True)
    dob = Column(Date, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now())


    def generate_uuid(first_name: str, client_id: str) -> uuid.UUID:
        namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # DNS namespace
        combined_key = f"{username}-{client_id}"
        return uuid.uuid5(namespace, combined_key)
    @staticmethod
    def copyToModel(person):
        personModel = PersonModel(**person.__dict__)
        personModel.__dict__.pop("_sa_instance_state", None)
        return personModel

    @staticmethod
    def copyFromModel(personModel):
        """Convert a single Pydantic DineinOrders model into a SQLAlchemy entity."""
        return Person(**personModel.dict(exclude_unset=True))


class User(Base):
    __tablename__ = "user"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    client_id = Column(String, nullable=False)
    roles = Column(ARRAY(String), default=[])
    grants = Column(ARRAY(String), default=[])


    def generate_uuid(username: str, client_id: str) -> uuid.UUID:
        namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # DNS namespace
        combined_key = f"{username}-{client_id}"
        return uuid.uuid5(namespace, combined_key)


    @staticmethod
    def copyToModel(user):
        """Convert SQLAlchemy User entities into Pydantic User models."""
        userModel = UserModel(**user.__dict__)
        userModel.__dict__.pop("_sa_instance_state", None)
        return userModel

    @staticmethod
    def copyFromModel(userModel):
        """Convert a single Pydantic DineinOrders model into a SQLAlchemy entity."""
        return User(**userModel.dict(exclude_unset=True))


    @staticmethod
    def copyToModels(users):
        """Convert SQLAlchemy User entities into Pydantic User models."""
        userModels = [UserModel(**user.__dict__) for user in users]

        # Remove SQLAlchemy metadata (_sa_instance_state)
        for model in userModels:
            model.__dict__.pop("_sa_instance_state", None)

        return userModels

    @staticmethod
    def copyFromModels(userModels):
        """Convert Pydantic User models into SQLAlchemy User entities."""
        return [User(**model.dict(exclude_unset=True)) for model in userModels]



@event.listens_for(User, "before_insert")
def set_uuid(mapper, connection, target):
    if not target.id and target.username and target.client_id:
        target.id = User.generate_uuid(target.username, target.client_id)


class PageDefinition(Base):
    __tablename__ = "page_definition"
    id = Column (Integer, primary_key=True, index=True)
    client_id = Column(String)
    role = Column(String)
    module = Column(String)
    operations = Column(ARRAY(String))
    screen_id = Column(String)
    load_type = Column(String)

    @staticmethod
    def copyToModels(page_definitions):
        """Convert SQLAlchemy PageDefinition entities into Pydantic models, removing metadata."""
        pageDefinitionModels = [PageDefinitionModel(**page_def.__dict__) for page_def in page_definitions]

        # Remove SQLAlchemy metadata (_sa_instance_state)
        for model in pageDefinitionModels:
            model.__dict__.pop("_sa_instance_state", None)

        return pageDefinitionModels

    @staticmethod
    def copyFromModels(page_models):
        """Convert Pydantic PageDefinition models into SQLAlchemy entities."""
        page_definitions = [
            PageDefinition(**model.dict(exclude_unset=True)) for model in page_models
        ]
        return page_definitions

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(String, nullable=False)
    template_name = Column(String, nullable=True)
    template_body = Column(String, nullable=True)
    type = Column(String, nullable=True)
    realm = Column(String, nullable=True)
    is_read = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now())    


class DelegatedAccess(Base):
    __tablename__ = "delegated_access"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requester_id = Column(UUID(as_uuid=True), nullable=False)   # waiter
    granted_by = Column(UUID(as_uuid=True), nullable=False)     # admin
    client_id = Column(String, nullable=False)
    resource = Column(String, nullable=False)                   # e.g., "orders"
    expires_at = Column(DateTime, nullable=False)