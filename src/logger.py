import logging
import os

LOG_FILE_PATH = os.path.join(os.getcwd(), "logs")
LOG_FILENAME = "Status.log"

os.makedirs(LOG_FILE_PATH, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_FILE_PATH, LOG_FILENAME),
    format="%(asctime)s: %(levelname)s:%(message)s ",
    level=logging.INFO,
)

logger = logging.getLogger()
