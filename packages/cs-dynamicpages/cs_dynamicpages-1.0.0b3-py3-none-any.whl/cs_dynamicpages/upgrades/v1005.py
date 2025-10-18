from . import logger
from plone import api
from cs_dynamicpages.utils import add_custom_view


def upgrade(setup_tool=None):
    """ """
    logger.info("Running upgrade (Python): Remove unneeded behaviors")

    registry_values = api.portal.get_registry_record(
        "cs_dynamicpages.dynamic_pages_control_panel.row_type_fields"
    )
    new_registry_values = []
    for registry_value in registry_values:
        if not registry_value.get("row_type_icon"):
            registry_value["row_type_icon"] = "bricks"
        new_registry_values.append(registry_value)
    api.portal.set_registry_record(
        "cs_dynamicpages.dynamic_pages_control_panel.row_type_fields",
        new_registry_values,
    )

    view_names = [view["row_type"] for view in new_registry_values]
    if "cs_dynamicpages-title-description-view" not in view_names:
        add_custom_view(
            "cs_dynamicpages-title-description-view",
            [
                "IBasic.title",
                "IBasic.description",
                "IRowWidth.width",
                "IExtraClass.extra_class",
            ],
            has_button=False,
            icon="fonts",
        )
        logger.info("Added new view")

    logger.info("Upgrade step run")
