import logging
import os
import sys
from colorama import Fore, Style, init
init(autoreset=True)

def setup_logger():
    logger = logging.getLogger("bitbot")
    logger.setLevel(logging.INFO)
    
    # File handler
    log_dir = "data/logs"
    os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler(f"{log_dir}/bot.log", encoding='utf-8')
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler dengan warna
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    class ColoredFormatter(logging.Formatter):
        COLORS = {
            logging.DEBUG: Fore.CYAN,
            logging.INFO: Fore.GREEN,
            logging.WARNING: Fore.YELLOW,
            logging.ERROR: Fore.RED,
            logging.CRITICAL: Fore.MAGENTA
        }
        def format(self, record):
            color = self.COLORS.get(record.levelno, Style.RESET_ALL)
            message = super().format(record)
            return f"{color}{message}{Style.RESET_ALL}"
    
    console_formatter = ColoredFormatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger
    
logger = setup_logger()