import logging
import logging.handlers
from typing import Optional

def setup_logging(log_file: Optional[str] = None, log_level: int = logging.INFO) -> None:
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler()]
    
    if log_file:
        # Add rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )