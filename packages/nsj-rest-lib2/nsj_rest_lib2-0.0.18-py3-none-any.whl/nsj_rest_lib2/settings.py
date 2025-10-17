import logging
import os

ESCOPO_RESTLIB2 = os.environ["ESCOPO_RESTLIB2"]
APP_NAME = os.getenv("APP_NAME", "nsj_rest_lib2")

ENV = os.getenv("ENV", "dev").lower()

if ENV in ("dev", "local"):
    MIN_TIME_SOURCE_REFRESH = 0
else:
    MIN_TIME_SOURCE_REFRESH = int(os.getenv("MIN_TIME_SOURCE_REFRESH", "15"))


def get_logger():
    return logging.getLogger(APP_NAME)
