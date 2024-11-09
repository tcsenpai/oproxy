import logging
from typing import Optional

def setup_logging(log_file: Optional[str] = None, log_level: int = logging.INFO) -> None:
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    if log_file:
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    else:
        logging.basicConfig(
            level=log_level,
            format=log_format
        )