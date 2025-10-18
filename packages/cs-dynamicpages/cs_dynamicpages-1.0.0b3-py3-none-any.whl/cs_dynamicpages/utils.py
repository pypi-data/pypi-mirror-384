from cs_dynamicpages import logger
from cs_dynamicpages.content.dynamic_page_row import IDynamicPageRow
from plone import api
from zope.component import getSiteManager
from zope.globalrequest import getRequest
from zope.interface import Interface
from zope.interface import providedBy


VIEW_PREFIX = "cs_dynamicpages-"


def add_custom_view(
    view_name: str,
    shown_fields: list[str],
    has_button: bool = False,
    icon: str = "bricks",
):
    """utility function to add a given view to the list of available row types"""
    record_name = "cs_dynamicpages.dynamic_pages_control_panel.row_type_fields"
    values = api.portal.get_registry_record(record_name)
    new_item = {
        "row_type": view_name,
        "each_row_type_fields": shown_fields,
        "row_type_has_featured_add_button": has_button,
        "row_type_icon": icon,
    }
    values.append(new_item)
    api.portal.set_registry_record(record_name, values)
    logger.info("Added new row type: %s", view_name)

    return True


def enable_behavior(behavior_dotted_name=str):
    """
    utility function to enable the given behavior in the DynamicPageRow content type
    """
    # Get the portal_types tool, which manages all content type definitions (FTIs)
    portal_types = api.portal.get_tool("portal_types")

    # Get the Factory Type Information (FTI) for our specific content type
    fti = getattr(portal_types, "DynamicPageRow", None)

    if not fti:
        # Failsafe in case the content type doesn't exist
        print("Content type 'DynamicPageRow' not found.")
        return

    # Get the current list of behaviors
    behaviors = list(fti.behaviors)

    # --- The Core Logic ---
    # Check if the behavior is already enabled to avoid duplicates
    if behavior_dotted_name not in behaviors:
        print(f"Enabling behavior '{behavior_dotted_name}' on 'DynamicPageRow'.")
        # Add the new behavior to the list
        behaviors.append(behavior_dotted_name)
        # Assign the updated list back to the FTI's behaviors attribute
        fti.behaviors = tuple(behaviors)
    else:
        print(
            f"Behavior '{behavior_dotted_name}' is already enabled on 'DynamicPageRow'."
        )


def get_available_views_for_row():
    items = []
    sm = getSiteManager()

    available_views = sm.adapters.lookupAll(
        required=(IDynamicPageRow, providedBy(getRequest())),
        provided=Interface,
    )

    values = api.portal.get_registry_record(
        "cs_dynamicpages.dynamic_pages_control_panel.row_type_fields", default=[]
    )

    for item in available_views:
        if item[0].startswith(VIEW_PREFIX):
            for value in values:
                item_dict = {
                    "row_type": item[0],
                    "each_row_type_fields": [],
                    "row_type_has_featured_add_button": False,
                    "row_type_icon": "bricks",
                }
                if item[0] == value["row_type"] and value not in items:
                    item_dict = value
                    items.append(item_dict)
    return items
