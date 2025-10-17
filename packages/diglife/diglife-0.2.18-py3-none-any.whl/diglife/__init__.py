from dotenv import load_dotenv, find_dotenv

dotenv_path = find_dotenv()
load_dotenv(".env", override=True)

from .log import Log
import logging
logger = Log(console_level = logging.WARNING, 
             log_file_name="app.log").logger

log_level = logger.critical
