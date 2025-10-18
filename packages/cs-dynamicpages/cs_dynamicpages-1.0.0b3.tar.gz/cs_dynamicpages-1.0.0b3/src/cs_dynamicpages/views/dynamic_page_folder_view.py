# from cs_dynamicpages import _
from cs_dynamicpages import _

# from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from cs_dynamicpages.utils import get_available_views_for_row
from plone import api
from plone.protect.interfaces import IDisableCSRFProtection
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from uuid import uuid4
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface import Interface


class IDynamicPageFolderView(Interface):
    """Marker Interface for IDynamicPageFolderView"""


@implementer(IDynamicPageFolderView)
class DynamicPageFolderView(BrowserView):
    # If you want to define a template here, please remove the template from
    # the configure.zcml registration of this view.
    # template = ViewPageTemplateFile('dynamic_page_folder_view.pt')

    def __call__(self):
        # Implement your own actions:
        return self.index()


@implementer(IDynamicPageFolderView)
class DynamicPageAddRowContentView(BrowserView):
    # If you want to define a template here, please remove the template from
    # the configure.zcml registration of this view.
    # template = ViewPageTemplateFile('dynamic_page_folder_view.pt')

    def __call__(self):
        # Implement your own actions:
        row_type = self.request.get("row_type")
        if row_type:
            random_id = uuid4()

            alsoProvides(self.request, IDisableCSRFProtection)
            api.content.create(
                type="DynamicPageRow",
                container=self.context,
                row_type=row_type,
                title=row_type,
                description="Here goes the description",
                id=str(random_id),
                link_text="Link Text",
                link_url="/",
            )
            available_views = get_available_views_for_row()
            for view in available_views:
                if view["row_type"] == row_type:
                    has_featured_button = view["row_type_has_featured_add_button"]
                    if has_featured_button:
                        created_elements_find = api.content.find(
                            portal_type="DynamicPageRow",
                            id=str(random_id),
                        )
                        created_element = created_elements_find[0].getObject()
                        random_id_featured = uuid4()
                        api.content.create(
                            type="DynamicPageRowFeatured",
                            container=created_element,
                            title="New Featured",
                            description="Here goes the description",
                            id=str(random_id_featured),
                            link_text="Link Text",
                            link_url="/",
                        )

                        random_id_featured_2 = uuid4()
                        api.content.create(
                            type="DynamicPageRowFeatured",
                            container=created_element,
                            title="New Featured 2",
                            description="Here goes the description",
                            id=str(random_id_featured_2),
                            link_text="Link Text",
                            link_url="/",
                        )
            statusmessage = _("Row added successfully")
            IStatusMessage(self.request).add(statusmessage, type="info")
            return self.request.response.redirect(
                f"{self.context.aq_parent.absolute_url()}#{random_id!s}"
            )
