import inspect
import os
from alembic import command
from alembic.config import Config as AlembicConfig
from sqlalchemy import create_engine
from contextlib import contextmanager
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from loguru import logger

from optrabot.config import Config

SQLALCHEMY_DATABASE_URL = "sqlite:///./optrabot.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def updateDatabase():
	logger.debug('Enter updateDatabase()')
	packageDirectory = os.path.dirname(inspect.getfile(Config))
	alembicConfigFile = packageDirectory + os.sep + 'alembic.ini'
	logger.debug('Package directory: {}  -> Alembic config: {}', packageDirectory, alembicConfigFile)
	scriptLocation = packageDirectory + os.sep + 'alembic'
	alembic_config = AlembicConfig(alembicConfigFile)
	alembic_config.set_main_option('script_location', scriptLocation)
	command.upgrade(alembic_config, "head")

def get_db_engine():
	return engine