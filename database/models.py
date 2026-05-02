from sqlalchemy import Column, Integer, BigInteger, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class SentProject(Base):
    """
    Persistent dedupe store: один рядок на project_id який ми вже надіслали в
    Telegram. Префікс freelancehunt_ ізолює таблицю в спільному Postgres.
    На SQLite (локальний dev) живе у bot_data.db.
    """
    __tablename__ = "freelancehunt_sent_projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
