from sqlalchemy.orm import declarative_base
import os

Base = declarative_base()

SCHEMA_NAME = os.getenv("DB_SCHEMA", "iso")
