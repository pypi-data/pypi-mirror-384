import logging
from loguru import logger
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# class InterceptHandler(logging.Handler):
# 	def emit(self, record):
# 		try:
# 			level = logger.level(record.levelname).name
# 		except ValueError:
# 			level = record.levelno
# 		if level == 'INFO':
# 			level = 'DEBUG'

# 		frame, depth = logging.currentframe(), 2
# 		while frame.f_code.co_filename == logging.__file__:
# 			frame = frame.f_back
# 			depth += 1

# 		logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
#if config.config_file_name is not None:
    # Alembic Logging messages should go to the OptraBot log
    #handler = InterceptHandler()
    #handlers = [handler]
    #alembiclogger = logging.basicConfig(level='INFO', handlers=handlers)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
