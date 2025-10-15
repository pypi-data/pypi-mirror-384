from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
import configparser,os

import logging,logging.config
l = logging.getLogger(__name__)


def configFromConfigPath(config_uri,initlogging=True):
  
  def getConfigCascade(config_uri):
    if not os.path.isfile(config_uri):
      l.warning("Config file %s not found, returning empty config"%config_uri)
      return []
      #raise ValueError("Config file %s not found"%config_uri)    
    here = os.path.dirname(config_uri)
    uricascade = []    
    temp_parser = configparser.ConfigParser()
    with open(config_uri,"r") as inifile:
      temp_parser.read_string(inifile.read())

    temp_parser['DEFAULT']['here'] = here
    temp_parser["app:main"]["here"] = here      
    use_directive = temp_parser.get('app:main', 'use', fallback=None)
    if use_directive and use_directive.startswith('config:'):
      base_config_path = use_directive.split('config:', 1)[1].strip()      
      l.debug("Loading base config %s (with here=%s)"%(base_config_path,here))
      uricascade += getConfigCascade(base_config_path)
    uricascade.append(config_uri)
    return uricascade

  config = configparser.ConfigParser() 
  
  configlist = getConfigCascade(config_uri)
  for i in configlist:
    l.info("Loading config file %s"%i)
    if not os.path.isfile(i):
      continue
    with open(i,"r") as inifile:
      config.read_string(inifile.read())
    here = os.path.dirname(configlist[-1])  
    config['DEFAULT']['here'] = here
    config["app:main"]["here"] = here
  if initlogging:    
    logging.config.fileConfig(config)
  return config

def engineFromConfigPath(config_uri,initlogging=True):
  config = configFromConfigPath(config_uri,initlogging)  
  return config,engineFromConfig(config)

def engineFromConfig(config):
  engine = engine_from_config(config["app:main"], "sqlalchemy.")
  return engine

def engineFromSettings(config):
  engine = engine_from_config(config, "sqlalchemy.")
  return engine

def factoryFormSettings(config):
  engine = engineFromSettings(config)
  session_factory = sessionmaker(bind=engine)
  return session_factory