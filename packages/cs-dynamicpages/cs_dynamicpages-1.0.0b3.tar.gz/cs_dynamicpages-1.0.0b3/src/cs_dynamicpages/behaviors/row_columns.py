from cs_dynamicpages import _
from plone import schema
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from Products.CMFPlone.utils import safe_hasattr
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import provider


class IRowColumnsMarker(Interface):
    pass


@provider(IFormFieldProvider)
class IRowColumns(model.Schema):
    """ """

    columns = schema.Choice(
        title=_("Column count"),
        description=_("Select how many columns will be shown in this row"),
        vocabulary="cs_dynamicpages.RowColumns",
        required=True,
        default="col-md-6",
    )


@implementer(IRowColumns)
@adapter(IRowColumnsMarker)
class RowColumns:
    def __init__(self, context):
        self.context = context

    @property
    def columns(self):
        if safe_hasattr(self.context, "columns"):
            return self.context.columns
        return None

    @columns.setter
    def columns(self, value):
        self.context.columns = value
