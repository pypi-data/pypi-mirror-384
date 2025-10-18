# from plone.app.textfield import RichText
# from plone.autoform import directives
from logging import getLogger
from plone import api
from plone.dexterity.content import Container

# from plone.namedfile import field as namedfile
from plone.supermodel import model

# from plone.supermodel.directives import fieldset
# from z3c.form.browser.radio import RadioFieldWidget
from zope import schema
from zope.interface import implementer


log = getLogger(__name__)

# from cs_dynamicpages import _


class IDynamicPageRow(model.Schema):
    """Marker interface and Dexterity Python Schema for DynamicPageRow"""

    row_type = schema.Choice(
        title="Row type",
        required=True,
        default="cs_dynamicpages-horizontal-rule-view",
        vocabulary="cs_dynamicpages.RowType",
    )


@implementer(IDynamicPageRow)
class DynamicPageRow(Container):
    """Content-type class for IPortadakoLerroa"""

    def row_template(self):
        return self.row_type.replace("cs_dynamicpages-", "")

    def review_state(self):
        return api.content.get_state(obj=self)

    def can_edit(self):
        return api.user.has_permission("Modify portal content", obj=self)

    def featured_list(self):
        return api.content.find(
            context=self,
            portal_type="DynamicPageRowFeatured",
            sort_on="getObjPositionInParent",
            depth=1,
        )

    def show_featured_add_button(self):
        row_type = self.row_type
        row_type_fields = api.portal.get_registry_record(
            "cs_dynamicpages.dynamic_pages_control_panel.row_type_fields"
        )
        for row_type_field in row_type_fields:
            if row_type_field["row_type"] == row_type:
                return row_type_field["row_type_has_featured_add_button"]
        return False

    def render(self, request):
        if self.row_type:
            try:
                view = api.content.get_view(
                    name=self.row_type,
                    context=self,
                    request=request,
                )
                return view()
            except Exception as e:
                log.error(e)
                return "ERROR RENDERING THE SELECTED ROW TYPE"
        return "THE SELECTED ROW TYPE IS NO LONGER AVAILABLE"
