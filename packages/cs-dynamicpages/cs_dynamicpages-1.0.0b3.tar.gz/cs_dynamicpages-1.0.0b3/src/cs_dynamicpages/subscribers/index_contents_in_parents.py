from Acquisition import aq_parent
from cs_dynamicpages import logger


def handler(obj, event):
    """When modifying a DynamicPageRow, we need to index the contents of the
    item where this row is shown.
    To do so we go up in the tree until we reach the content and force
    the reindex of it.
    """
    dynamic_page_folder = aq_parent(obj)
    if dynamic_page_folder.portal_type == "DynamicPageFolder":
        content = aq_parent(dynamic_page_folder)
        content.reindexObject()
        logger.info("Reindex item: %s", "/".join(content.getPhysicalPath()))
