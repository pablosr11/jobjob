from typing import Dict

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


def create_db_str(config: Dict) -> str:
    return f'postgres://{config.get("db_user")}:{config.get("db_pass")}@{config.get("db_server")}/{config.get("db_name")}'

db_config = {
    "db_user": "postgres",
    "db_pass": "postgres",
    "db_server": "db",
    "db_name": "postgres"
}
SQLALCHEMY_DATABASE_URL = create_db_str(db_config)

# create db engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Each instance of SessionLocal will be a db session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# We will inherit from Base to generate the DB models
Base = declarative_base()
