import os
from pathlib import Path

import dotenv

dotenv.load_dotenv()

PLANT_API_KEY = os.getenv('PLANT_API_KEY')
INSECT_API_KEY = os.getenv('INSECT_API_KEY')
MUSHROOM_API_KEY = os.getenv('MUSHROOM_API_KEY')
CROP_HEALTH_API_KEY = os.getenv('CROP_HEALTH_API_KEY')

APP_DIR = Path(__file__).resolve().parent

ENVIRONMENT = os.getenv('ENVIRONMENT', 'STAGING')
assert ENVIRONMENT in {'LOCAL', 'STAGING', 'PRODUCTION'}, (
    f'Invalid environment: {ENVIRONMENT}; ' f'must be one of `LOCAL`, `STAGING`, `PRODUCTION`'
)
