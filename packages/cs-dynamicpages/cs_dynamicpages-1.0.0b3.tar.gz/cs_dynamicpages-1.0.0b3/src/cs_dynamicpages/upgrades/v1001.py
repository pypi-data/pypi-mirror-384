from . import logger


# from plone import api


def upgrade(setup_tool=None):
    """ """
    logger.info("Running upgrade (Python): Add row width field in the controlpanel")
