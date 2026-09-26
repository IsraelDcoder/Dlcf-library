import logging

from flask import current_app
from alembic import context


config = context.config
if config.config_file_name:
    logging.config.fileConfig(config.config_file_name)


def get_engine():
    database = current_app.extensions['migrate'].db
    try:
        return database.get_engine()
    except (TypeError, AttributeError):
        return database.engine


def get_metadata():
    database = current_app.extensions['migrate'].db
    if hasattr(database, 'metadatas'):
        return database.metadatas[None]
    return database.metadata


def configure_context(**kwargs):
    context.configure(
        target_metadata=get_metadata(),
        **kwargs,
    )


def run_migrations_offline():
    url = get_engine().url.render_as_string(hide_password=False)
    configure_context(url=url, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    with get_engine().connect() as connection:
        configure_context(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()