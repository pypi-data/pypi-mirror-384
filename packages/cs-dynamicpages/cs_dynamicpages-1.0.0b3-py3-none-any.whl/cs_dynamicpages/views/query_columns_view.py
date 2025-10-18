# from cs_dynamicpages import _
from cs_dynamicpages.views.dynamic_page_row_view import DynamicPageRowView
from plone.app.contenttypes.browser.collection import CollectionView
from zope.interface import implementer
from zope.interface import Interface


# from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class IQueryColumnsView(Interface):
    """Marker Interface for IQueryColumnsView"""


@implementer(IQueryColumnsView)
class QueryColumnsView(CollectionView, DynamicPageRowView):
    # If you want to define a template here, please remove the template from
    # the configure.zcml registration of this view.
    # template = ViewPageTemplateFile('query_columns_view.pt')

    def __call__(self):
        # Implement your own actions:
        return self.index()
