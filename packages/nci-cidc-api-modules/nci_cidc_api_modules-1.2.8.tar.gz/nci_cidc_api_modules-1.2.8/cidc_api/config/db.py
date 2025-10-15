from os import environ

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import declarative_base
from google.cloud.sql.connector import Connector, IPTypes

from .secrets import get_secrets_manager

db = SQLAlchemy()
BaseModel = declarative_base()
db.Model = BaseModel

connector = Connector()


def getconn():
    return connector.connect(
        environ.get("CLOUD_SQL_INSTANCE_NAME"),
        "pg8000",
        user=environ.get("CLOUD_SQL_DB_USER"),
        password="xxxxx",
        db=environ.get("CLOUD_SQL_DB_NAME"),
        enable_iam_auth=True,
        ip_type=IPTypes.PUBLIC,
    )


def init_db(app: Flask):
    """Connect `app` to the database and run migrations"""
    db.init_app(app)
    db.Model = BaseModel
    Migrate(app, db, app.config["MIGRATIONS_PATH"])
    with app.app_context():
        upgrade(app.config["MIGRATIONS_PATH"])


def get_sqlalchemy_database_uri(testing: bool = False) -> str:
    """Get the PostgreSQL DB URI from environment variables"""

    db_uri = environ.get("POSTGRES_URI")
    if testing:
        # Connect to the test database
        db_uri = environ.get("TEST_POSTGRES_URI", "fake-conn-string")
    elif not db_uri:
        db_uri = f"postgresql+pg8000://{environ.get('CLOUD_SQL_DB_USER')}:xxx@/{environ.get('CLOUD_SQL_DB_NAME')}"

    assert db_uri

    return db_uri


# Use SQLALCHEMY_ENGINE_OPTIONS to connect to the cloud but use uri for local db
def cloud_connector(testing: bool = False):
    if not testing and not environ.get("POSTGRES_URI"):
        return {"creator": getconn}
    else:
        return {}
