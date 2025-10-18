# from cs_dynamicpages import _
from cs_dynamicpages.utils import get_available_views_for_row
from plone import api
from plone.protect.interfaces import IDisableCSRFProtection
from Products.Five.browser import BrowserView
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface import Interface


class IDynamicView(Interface):
    """Marker Interface for IDynamicView"""


@implementer(IDynamicView)
class DynamicView(BrowserView):
    def rows(self):
        dynamic_page_folder = self.dynamic_page_folder_element()
        if dynamic_page_folder:
            return api.content.find(
                portal_type="DynamicPageRow",
                sort_on="getObjPositionInParent",
                context=dynamic_page_folder,
            )
        return []

    def dynamic_page_folder_element(self):
        page_folders = api.content.find(
            portal_type="DynamicPageFolder",
            context=self.context,
            depth=1,
            sort_on="getObjPositionInParent",
        )
        if page_folders:
            return page_folders[0].getObject()
        else:
            if self.can_edit():
                alsoProvides(self.request, IDisableCSRFProtection)
                api.content.create(
                    container=self.context,
                    type="DynamicPageFolder",
                    title="Rows",
                )
                created_elements_find = api.content.find(
                    portal_type="DynamicPageFolder",
                    context=self.context,
                    depth=1,
                    sort_on="getObjPositionInParent",
                )
                created_element = created_elements_find[0].getObject()
                api.content.transition(created_element, transition="publish")
                return created_element

    def dynamic_page_folder_element_url(self):
        dynamic_page_folder = self.dynamic_page_folder_element()
        if dynamic_page_folder:
            return dynamic_page_folder.absolute_url()
        return ""

    def can_edit(self):
        return api.user.has_permission("Modify portal content", obj=self.context)

    def available_views_for_row(self):
        return get_available_views_for_row()
