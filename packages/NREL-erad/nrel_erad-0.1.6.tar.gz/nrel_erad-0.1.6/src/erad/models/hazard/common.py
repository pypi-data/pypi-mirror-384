from pathlib import Path

from loguru import logger
import requests


TEST_PATH = Path(__file__).parents[4] / "tests"
DATA_FOLDER_NAME = "data"
DATA_FOLDER = TEST_PATH / DATA_FOLDER_NAME
DB_FILENAME = "erad_data.sqlite"
ERAD_DB = TEST_PATH / DATA_FOLDER_NAME / DB_FILENAME
BUCKET_NAME = "erad_v2_dataset"

if not ERAD_DB.exists():
    logger.info("Erad database not found. Downloading from Google Cloud.")
    ERAD_DB.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://storage.googleapis.com/{BUCKET_NAME}/{DB_FILENAME}"
    response = requests.get(url)

    with open(ERAD_DB, "wb") as f:
        f.write(response.content)
    logger.info("Download complete...")

HISTROIC_EARTHQUAKE_TABLE = "historic_earthquakes"
HISTROIC_HURRICANE_TABLE = "historic_hurricanes"
HISTROIC_FIRE_TABLE = "historic_fires"
