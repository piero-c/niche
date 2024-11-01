import json
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path('../db/.env'))

def load_config():
    """Load config based on env
    """
    env = os.getenv('NODE_ENV')
    with open(Path('scripts/db/config.json')) as config_file:
        config = json.load(config_file)
    return(config.get(env))
