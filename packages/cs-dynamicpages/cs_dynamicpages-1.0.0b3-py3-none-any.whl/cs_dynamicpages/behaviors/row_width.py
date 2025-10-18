from cs_dynamicpages import _
from plone import schema
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from Products.CMFPlone.utils import safe_hasattr
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import provider


class IRowWidthMarker(Interface):
    pass


@provider(IFormFieldProvider)
class IRowWidth(model.Schema):
    width = schema.Choice(
        title=_("Row width"),
        description=_("Select the width that this row will have"),
        vocabulary="cs_dynamicpages.RowWidth",
        required=True,
        default="col-md-12",
    )


@implementer(IRowWidth)
@adapter(IRowWidthMarker)
class RowWidth:
    def __init__(self, context):
        self.context = context

    @property
    def width(self):
        if safe_hasattr(self.context, "width"):
            return self.context.width
        return None

    @width.setter
    def width(self, value):
        self.context.width = value
