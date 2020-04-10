from typing import Dict
from os import environ

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


def create_db_str(config: Dict) -> str:
    return f'postgres://{config.get("user")}:{config.get("pass")}@{config.get("host")}/{config.get("name")}'

db_config = {
    "user": "postgres",
    "pass": "postgres",
    "host": "db",
    "name": "postgres"
}
SQLALCHEMY_DATABASE_URL = create_db_str(db_config)

# create db engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=False)

# Each instance of SessionLocal will be a db session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# We will inherit from Base to generate the DB models
Base = declarative_base()
