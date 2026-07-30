from __future__ import with_statement

import sys
from logging.config import fileConfig

from alembic import context

from sqlalchemy import engine_from_config, pool

sys.path.insert(0, "")

from app.config import get_settings  # noqa: E402
from app.database import Base  # noqa: E402
from app.models import simulacao  # noqa: F401,E402


# Eu configuro o Alembic para usar a URL definida nas configurações da aplicação
config = context.config
fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
