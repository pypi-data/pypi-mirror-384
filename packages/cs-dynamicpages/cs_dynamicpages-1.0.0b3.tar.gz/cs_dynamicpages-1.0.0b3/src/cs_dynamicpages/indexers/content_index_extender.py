from plone import api
from plone.app.dexterity import textindexer
from plone.dexterity.interfaces import IDexterityContainer
from zope.component import adapter
from zope.interface import implementer


def extract_text_value_to_index(content):
    """convert the text field of a content item to plain text"""
    text = (content.text and content.text.output) or ""
    pt = api.portal.get_tool("portal_transforms")
    data = pt.convertTo("text/plain", text, mimetype="text/html")
    return data.getData()


FIELDS_TO_INDEX = {
    # Full field name: function to get the indexed value
    "IBasic.title": lambda content: content.Title(),
    "IBasic.description": lambda content: content.Description(),
    "IRichTextBehavior-text": extract_text_value_to_index,
}


@implementer(textindexer.IDynamicTextIndexExtender)
@adapter(IDexterityContainer)
class FolderishItemTextExtender:
    def __init__(self, context):
        self.context = context

    def __call__(self):
        layout = self.context.getLayout()
        if layout == "dynamic-view":
            return get_available_text_from_dynamic_pages(self.context)
        return ""


def get_enabled_fields(row_type):
    """return the fields that are enabled to be edited in the given
    row type
    """
    row_type_fields = api.portal.get_registry_record(
        "cs_dynamicpages.dynamic_pages_control_panel.row_type_fields"
    )

    for item in row_type_fields:
        if item["row_type"] == row_type:
            return item["each_row_type_fields"]

    return []


def get_available_text_from_dynamic_pages(context):
    """this should return the indexable texts
    for a given dynamic page

    it should extract the texts from the row container in the context
    """
    value = []
    brains = api.content.find(
        portal_type="DynamicPageRow",
        review_state="published",
        context=context,
    )
    for brain in brains:
        drr = brain.getObject()
        enabled_fields = get_enabled_fields(drr.row_type)
        for enabled_field in enabled_fields:
            extract_content_function = FIELDS_TO_INDEX.get(enabled_field)
            if extract_content_function is not None:
                value.append(extract_content_function(drr))

    return " ".join(value)
