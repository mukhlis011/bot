# src/utils.py
import logging
import os

def setup_logger():
    """
    Setup logger untuk menyimpan aktivitas bot ke file
    """
    log_dir = "data/logs"
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        filename=f"{log_dir}/bot.log",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    console.setFormatter(formatter)
    logging.getLogger().addHandler(console)
    return logging.getLogger(__name__)