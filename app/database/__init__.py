from app.config import DATABASE_USER, DATABASE_PASS, DATABASE_HOST, DATABASE_NAME
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database conn credentials
db_user = DATABASE_USER
db_pass = DATABASE_PASS
db_host = DATABASE_HOST
db_name = DATABASE_NAME

# Init database
db_url = "postgresql://{0}:{1}@{2}/{3}".format(db_user, db_pass, db_host, db_name)
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
