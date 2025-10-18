from cs_dynamicpages import _
from plone import schema
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from Products.CMFPlone.utils import safe_hasattr
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import provider


class ILinkInfoMarker(Interface):
    pass


@provider(IFormFieldProvider)
class ILinkInfo(model.Schema):
    """ """

    link_text = schema.TextLine(
        title=_("Link text"),
        description=_("Enter the text that will be linked"),
        required=False,
    )

    link_url = schema.TextLine(
        title=_("Link URL"),
        description=_("Enter the URL of the link"),
        required=False,
    )


@implementer(ILinkInfo)
@adapter(ILinkInfoMarker)
class LinkInfo:
    def __init__(self, context):
        self.context = context

    @property
    def link_text(self):
        if safe_hasattr(self.context, "link_text"):
            return self.context.link_text
        return None

    @link_text.setter
    def link_text(self, value):
        self.context.link_text = value

    @property
    def link_url(self):
        if safe_hasattr(self.context, "link_url"):
            return self.context.link_url
        return None

    @link_url.setter
    def link_url(self, value):
        self.context.link_url = value
