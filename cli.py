import logging
import os


def cli(cmd):
    logging.info(cmd)
    os.system(cmd)
