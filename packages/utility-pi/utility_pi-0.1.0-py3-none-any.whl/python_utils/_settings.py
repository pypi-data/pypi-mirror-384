from logging.config import dictConfig
import yaml

with open("./logging.yaml", "r") as f:
    log_config = yaml.safe_load(f)

dictConfig(log_config)
