from dotenv  import load_dotenv
from pathlib import Path

import json
import os

load_dotenv(Path('./config/.env'))

def load_config():
    """Load config based on env
    """
    env = os.getenv('ENV')
    with open(Path('./config/config.json')) as config_file:
        config = json.load(config_file)
    return(config.get(env))
