from . import logger
from cs_dynamicpages.controlpanels.dynamic_pages_control_panel.controlpanel import (
    IDynamicPagesControlPanel,
)
from plone import api
from plone.app.upgrade.utils import alias_module
from zope.annotation.interfaces import IAnnotations


# from plone import api
import json


alias_module(
    "cs_dynamicpages.controlpanels.dynamica_pages_control_panel.controlpanel.IDynamicaPagesControlPanel",
    IDynamicPagesControlPanel,
)


def upgrade(setup_tool=None):
    """ """
    logger.info("Running upgrade (Python): Change Control Panel name in registry")


UPGRADEABLE_KEYS = ["row_type_fields", "row_widths"]


def pre_handler(setup_tool=None):
    """ """
    for key in UPGRADEABLE_KEYS:
        value = api.portal.get_registry_record(
            f"cs_dynamicpages.dynamica_pages_control_panel.{key}", default=[]
        )

        value_str = json.dumps(value)
        portal = api.portal.get()
        IAnnotations(portal)[
            f"cs_dynamicpages.dynamic_pages_control_panel.{key}.UPGRADE"
        ] = value_str

    logger.info("Save existing values for upgrade")


def post_handler(setup_tool=None):
    """ """
    portal = api.portal.get()
    for key in UPGRADEABLE_KEYS:
        annotated = IAnnotations(portal)
        value_str = annotated.get(
            f"cs_dynamicpages.dynamic_pages_control_panel.{key}.UPGRADE", "[]"
        )
        try:
            value = json.loads(value_str)
        except Exception:
            value = []
        if not isinstance(value, list):
            value = []
        api.portal.set_registry_record(
            f"cs_dynamicpages.dynamic_pages_control_panel.{key}", value
        )

        del annotated[f"cs_dynamicpages.dynamic_pages_control_panel.{key}.UPGRADE"]

    logger.info("Restored existing values after upgrade")
