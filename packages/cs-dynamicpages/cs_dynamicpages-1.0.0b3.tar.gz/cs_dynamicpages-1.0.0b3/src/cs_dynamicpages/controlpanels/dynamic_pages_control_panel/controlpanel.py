from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.registry import DictRow
from cs_dynamicpages import _
from cs_dynamicpages.interfaces import IBrowserLayer
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.autoform.directives import widget
from plone.restapi.controlpanels import RegistryConfigletPanel
from plone.z3cform import layout
from zope import schema
from zope.component import adapter
from zope.interface import Interface


class IRowTypeFieldsSchema(Interface):
    row_type = schema.Choice(
        title=_("Row type"),
        required=True,
        vocabulary="cs_dynamicpages.RowType",
    )

    each_row_type_fields = schema.List(
        title=_("Row fields"),
        description=_(
            "Enter the fields that will be available when "
            "editing this row type. This is useful to hide unused fields."
        ),
        required=True,
        value_type=schema.TextLine(),
        default=[],
    )

    row_type_has_featured_add_button = schema.Bool(
        title=_("Has featured add button?"),
        description=_(
            "If selected a 'Add featured' button will be added in the edit "
            "interface. This is useful for rows that have content pieces "
            "inside them. For example in a slider row, there are slider items. "
            "This button will be used to add those items."
        ),
        required=False,
        default=False,
    )

    row_type_icon = schema.TextLine(
        title=_("Row type icon"),
        description=_("Icon for the row type"),
        required=True,
        default="bricks",
    )


class IRowWidthSchema(Interface):
    row_width_label = schema.TextLine(
        title=_("Row Width Label"),
        description=_("This is the label corresponding to this width"),
        required=True,
    )

    row_width_class = schema.TextLine(
        title=_("Row Width CSS class"),
        description=_("CSS class for the row width"),
        required=True,
    )


class IDynamicPagesControlPanel(Interface):
    widget(row_type_fields=DataGridFieldFactory)
    row_type_fields = schema.List(
        title=_("Row type fields"),
        description=_(
            "Here we have all the available views for the rows and their settings"
        ),
        required=True,
        value_type=DictRow(title=_("Row type field"), schema=IRowTypeFieldsSchema),
        default=[
            {
                "row_type": "cs_dynamicpages-title-description-view",
                "each_row_type_fields": [
                    "IBasic.title",
                    "IBasic.description",
                    "IRowWidth.width",
                    "IExtraClass.extra_class",
                ],
                "row_type_has_featured_add_button": False,
                "row_type_icon": "fonts",
            },
            {
                "row_type": "cs_dynamicpages-featured-view",
                "each_row_type_fields": [
                    "IBasic.title",
                    "IBasic.description",
                    "IRowWidth.width",
                    "IExtraClass.extra_class",
                    "IRelatedImage.related_image",
                    "IRelatedImage.image_position",
                    "ILinkInfo.link_text",
                    "ILinkInfo.link_url",
                ],
                "row_type_has_featured_add_button": False,
                "row_type_icon": "card-image",
            },
            {
                "row_type": "cs_dynamicpages-featured-overlay-view",
                "each_row_type_fields": [
                    "IBasic.title",
                    "IBasic.description",
                    "IRowWidth.width",
                    "IExtraClass.extra_class",
                    "IRelatedImage.related_image",
                    "ILinkInfo.link_text",
                    "ILinkInfo.link_url",
                ],
                "row_type_has_featured_add_button": False,
                "row_type_icon": "image-fill",
            },
            {
                "row_type": "cs_dynamicpages-horizontal-rule-view",
                "each_row_type_fields": [
                    "IBasic.title",
                    "IRowWidth.width",
                    "IExtraClass.extra_class",
                ],
                "row_type_has_featured_add_button": False,
                "row_type_icon": "hr",
            },
            {
                "row_type": "cs_dynamicpages-spacer-view",
                "each_row_type_fields": [
                    "IBasic.title",
                    "IExtraClass.extra_class",
                ],
                "row_type_has_featured_add_button": False,
                "row_type_icon": "arrows-vertical",
            },
            {
                "row_type": "cs_dynamicpages-slider-view",
                "each_row_type_fields": [
                    "IBasic.title",
                    "IRowWidth.width",
                    "IExtraClass.extra_class",
                ],
                "row_type_has_featured_add_button": True,
                "row_type_icon": "images",
            },
            {
                "row_type": "cs_dynamicpages-features-view",
                "each_row_type_fields": [
                    "IBasic.title",
                    "IRowWidth.width",
                    "IExtraClass.extra_class",
                ],
                "row_type_has_featured_add_button": True,
                "row_type_icon": "grid",
            },
            {
                "row_type": "cs_dynamicpages-accordion-view",
                "each_row_type_fields": [
                    "IBasic.title",
                    "IRowWidth.width",
                    "IExtraClass.extra_class",
                ],
                "row_type_has_featured_add_button": True,
                "row_type_icon": "chevron-double-down",
            },
            {
                "row_type": "cs_dynamicpages-query-columns-view",
                "each_row_type_fields": [
                    "IBasic.title",
                    "IRowWidth.width",
                    "IExtraClass.extra_class",
                    "ICollection.query",
                    "ICollection.sort_on",
                    "ICollection.sort_order",
                    "ICollection.betweeen",
                    "ICollection.limit",
                    "IRowColumns.columns",
                ],
                "row_type_has_featured_add_button": False,
                "row_type_icon": "funnel",
            },
            {
                "row_type": "cs_dynamicpages-text-view",
                "each_row_type_fields": [
                    "IBasic.title",
                    "IRowWidth.width",
                    "IExtraClass.extra_class",
                    "IRichTextBehavior-text",
                ],
                "row_type_has_featured_add_button": False,
                "row_type_icon": "body-text",
            },
        ],
    )

    widget(row_widths=DataGridFieldFactory)
    row_widths = schema.List(
        title=_("Row widths"),
        description=_("Here you can define the available widths for each row"),
        required=True,
        value_type=DictRow(
            title=_("Row width"),
            schema=Interface(
                IRowWidthSchema,
            ),
        ),
        default=[
            {
                "row_width_label": "Narrow",
                "row_width_class": "col-md-6 offset-md-3",
            },
            {
                "row_width_label": "Centered",
                "row_width_class": "col-md-8 offset-md-2",
            },
            {
                "row_width_label": "Full width",
                "row_width_class": "col-md-12",
            },
        ],
    )


class DynamicPagesControlPanel(RegistryEditForm):
    schema = IDynamicPagesControlPanel
    schema_prefix = "cs_dynamicpages.dynamic_pages_control_panel"
    label = _("Dynamic Pages Control Panel")


DynamicPagesControlPanelView = layout.wrap_form(
    DynamicPagesControlPanel, ControlPanelFormWrapper
)


@adapter(Interface, IBrowserLayer)
class DynamicPagesControlPanelConfigletPanel(RegistryConfigletPanel):
    """Control Panel endpoint"""

    schema = IDynamicPagesControlPanel
    configlet_id = "dynamic_pages_control_panel-controlpanel"
    configlet_category_id = "Products"
    title = _("Dynamic Pages Control Panel")
    group = ""
    schema_prefix = "cs_dynamicpages.dynamic_pages_control_panel"
