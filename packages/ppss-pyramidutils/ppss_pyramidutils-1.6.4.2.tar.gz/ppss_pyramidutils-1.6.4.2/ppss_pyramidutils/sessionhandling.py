from contextlib import contextmanager

import time
import logging
l = logging.getLogger(__name__)

################# create session factory from pyramid settings
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker

def engineFromSettings(config):
  engine = engine_from_config(config, "sqlalchemy.")
  return engine

def factoryFormSettings(config):
  session_factory = None
  try:
    engine = engineFromSettings(config)
    session_factory = sessionmaker(bind=engine)
  except Exception as e:
    l.exception("can't create session factory")
    time.sleep(10)
  return session_factory


#### allow usage of "with" clause with session
@contextmanager
def session_scope(sessionFactory):
    session = sessionFactory()
    l.debug ("new session created")
    try:
        yield session
        l.debug ("committing")
        session.commit()
    except Exception as e:
        session.rollback()
        l.exception("rollback for exception {}".format(e))
        raise e
    finally:
        session.close()
        l.debug ("session closed")