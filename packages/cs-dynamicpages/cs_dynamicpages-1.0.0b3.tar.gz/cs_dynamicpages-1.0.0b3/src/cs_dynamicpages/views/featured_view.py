# from cs_dynamicpages import _
from cs_dynamicpages.views.dynamic_page_row_view import DynamicPageRowView
from zope.interface import implementer
from zope.interface import Interface


class IFeaturedView(Interface):
    """Marker Interface for IFeaturedView"""


@implementer(IFeaturedView)
class FeaturedView(DynamicPageRowView):
    def related_image(self):
        related_image = self.context.related_image
        if related_image:
            return related_image[0].to_object
        return None
