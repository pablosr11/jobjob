from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

db_user = "postgres"
db_pass = "postgres"
db_server = "db"
# db_server = "localhost"
db_name = "postgres"
SQLALCHEMY_DATABASE_URL = f"postgres://{db_user}:{db_pass}@{db_server}/{db_name}"

# create db engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Each instance of SessionLocal will be a db session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# We will inherit from Base to generate the DB models
Base = declarative_base()
