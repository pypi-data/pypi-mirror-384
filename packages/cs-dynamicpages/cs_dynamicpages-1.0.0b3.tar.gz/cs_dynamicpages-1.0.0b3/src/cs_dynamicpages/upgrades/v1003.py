from . import logger
from .base import reload_gs_profile


# from plone import api


def upgrade(setup_tool=None):
    """ """
    logger.info("Running upgrade (Python): Add a new default behavior to the row")
    reload_gs_profile(setup_tool)
