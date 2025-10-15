import os
import sqlalchemy
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from google.cloud.sql.connector import Connector, IPTypes
import pg8000.dbapi

PROJECT_ID = "saas-user-service"
REGION = "asia-south2"
INSTANCE_NAME = "saas-473815"
DB_USER = "postgres"
DB_PASS = "Saasqa@123"
DB_NAME = "postgres"

Base = declarative_base()

def get_db() -> sqlalchemy.engine.base.Engine:
    """
    Initializes a connection pool for a Cloud SQL instance of Postgres.

    Uses the Cloud SQL Python Connector package.
    """
    # Note: Saving credentials in environment variables is convenient, but not
    # secure - consider a more secure solution such as
    # Cloud Secret Manager (https://cloud.google.com/secret-manager) to help
    # keep secrets safe.

    ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC

    # initialize Cloud SQL Python Connector object
    connector = Connector(refresh_strategy="LAZY")

    def getconn() -> pg8000.dbapi.Connection:
        conn: pg8000.dbapi.Connection = connector.connect(
            f"{PROJECT_ID}:{REGION}:{INSTANCE_NAME}",
            "pg8000", # Or "psycopg2" if you installed psycopg2-binary
            user=DB_USER,
            password=DB_PASS,
            db=DB_NAME,
            ip_type=IPTypes.PUBLIC,
        )
        return conn

    # The Cloud SQL Python Connector can be used with SQLAlchemy
    # using the 'creator' argument to 'create_engine'
    pool = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        # ...
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=pool)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

    return db