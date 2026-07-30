from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


# Eu defino a Base declarativa para os modelos SQLAlchemy. Mantive simples para compatibilidade.
class Base(DeclarativeBase):
    pass


# Eu crio o engine usando a URL das configurações. `pool_pre_ping` ajuda a evitar
# conexões staled em ambientes com containers que reiniciam.
engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    # Eu forneço um gerador para injetar a sessão no FastAPI via Depends.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> bool:
    # Eu faço um healthcheck simples executando um SELECT 1.
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True
