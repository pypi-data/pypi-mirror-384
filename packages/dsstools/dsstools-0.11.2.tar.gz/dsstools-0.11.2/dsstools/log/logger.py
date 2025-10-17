import json
import logging
import logging.config
from importlib.resources import files

def setup_logging():
    """Set up logging according to the config file."""
    logroot = files("dsstools") / "log"
    with open(logroot / 'config.json', 'r', encoding="UTF-8") as config_file:
        config = json.load(config_file)
        logging.config.dictConfig(config)
    logging.basicConfig(filename=logroot / "logs/report.log")

setup_logging()

def get_logger(name: str):
    """Return logger name."""
    return logging.getLogger(name)
