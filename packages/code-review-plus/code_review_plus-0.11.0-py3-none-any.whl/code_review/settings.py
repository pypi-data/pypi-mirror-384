import logging.config
from pathlib import Path

from rich.console import Console

from code_review.config import get_config

CLI_CONSOLE = Console()

CODE_REVIEW_FOLDER = Path(__file__).home() / "Documents" / "code_review"
if not CODE_REVIEW_FOLDER.exists():
    CODE_REVIEW_FOLDER.mkdir(parents=True, exist_ok=True)

BASE_FOLDER = Path(__file__).parent.parent
OUTPUT_FOLDER = BASE_FOLDER / "output"

# Define log directory
LOG_DIR = OUTPUT_FOLDER / "logs"
if not LOG_DIR.exists():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

BANNER = """
 ██████╗ ██████╗ ██████╗ ███████╗    ██████╗ ███████╗██╗   ██╗██╗███████╗██╗    ██╗    ██████╗ ██╗     ██╗   ██╗███████╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔══██╗██╔════╝██║   ██║██║██╔════╝██║    ██║    ██╔══██╗██║     ██║   ██║██╔════╝
██║     ██║   ██║██║  ██║█████╗      ██████╔╝█████╗  ██║   ██║██║█████╗  ██║ █╗ ██║    ██████╔╝██║     ██║   ██║███████╗
██║     ██║   ██║██║  ██║██╔══╝      ██╔══██╗██╔══╝  ╚██╗ ██╔╝██║██╔══╝  ██║███╗██║    ██╔═══╝ ██║     ██║   ██║╚════██║
╚██████╗╚██████╔╝██████╔╝███████╗    ██║  ██║███████╗ ╚████╔╝ ██║███████╗╚███╔███╔╝    ██║     ███████╗╚██████╔╝███████║
 ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚═╝  ╚═╝╚══════╝  ╚═══╝  ╚═╝╚══════╝ ╚══╝╚══╝     ╚═╝     ╚══════╝ ╚═════╝ ╚══════╝                                                                                                                   
"""
TAGLINE = "Code Review Plus - Enhancing Your Code Review Experience"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        "detailed": {"format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": str(LOG_DIR / "code_review.log"),
            "mode": "a",
        },
    },
    "loggers": {
        "code_review": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "code_review.review.main": {
            "level": "DEBUG",
            "handlers": [
                "console",
            ],
            "propagate": False,
        },
        "code_review.schemas": {
            "level": "INFO",
            "handlers": [
                "console",
            ],
            "propagate": False,
        },
        "code_review.dependencies.pip.handlers": {
            "level": "INFO",
            "handlers": [
                "console",
            ],
            "propagate": False,
        },
        "code_review.git": {
            "level": "DEBUG",
            "handlers": [
                # "console",
                "file"
            ],
            "propagate": False,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
}

# Configure logging when the module is imported
logging.config.dictConfig(LOGGING)

CURRENT_CONFIGURATION = get_config()
