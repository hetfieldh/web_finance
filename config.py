# web_finance/config.py

import logging
import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_ENV = os.environ.get("FLASK_ENV")

    LOG_TO_STDOUT = os.environ.get("LOG_TO_STDOUT")
    LOG_FILE = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "logs", "web_finance.log"
    )
    LOG_LEVEL = logging.INFO

    LOG_MAX_BYTES = 1024 * 1024 * 5
    LOG_BACKUP_COUNT = 5
