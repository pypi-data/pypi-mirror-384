from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from delta.run.config import Settings


engine = create_engine(
    url=str(Settings().database_url),
    echo=bool(Settings().database_show_sql),
)

Session = sessionmaker(bind=engine, autoflush=True)
