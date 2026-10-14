
from sqlalchemy import create_engine

DATABASE_URL = (
    "mysql+pymysql://user:password@localhost:3306/biblioteca_jdbc"
)

engine = create_engine(DATABASE_URL)
