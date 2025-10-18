# from cs_dynamicpages import _
from cs_dynamicpages.views.dynamic_page_row_view import DynamicPageRowView
from plone import api
from zope.interface import implementer
from zope.interface import Interface


class ISliderView(Interface):
    """Marker Interface for ISliderView"""


@implementer(ISliderView)
class SliderView(DynamicPageRowView):
    # If you want to define a template here, please remove the template from
    # the configure.zcml registration of this view.
    # template = ViewPageTemplateFile('slider_view.pt')

    def elements(self):
        # Implement your own actions:
        return api.content.find(
            portal_type="DynamicPageRowFeatured",
            context=self.context,
            sort_on="getObjPositionInParent",
        )
