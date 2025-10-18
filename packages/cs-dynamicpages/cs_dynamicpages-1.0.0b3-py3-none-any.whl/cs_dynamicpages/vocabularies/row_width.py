# from plone import api
from plone import api
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class VocabItem:
    def __init__(self, token, value):
        self.token = token
        self.value = value


@implementer(IVocabularyFactory)
class RowWidth:
    """ """

    def __call__(self, context):
        # Just an example list of content for our vocabulary,
        # this can be any static or dynamic data, a catalog result for example.
        values = api.portal.get_registry_record(
            "cs_dynamicpages.dynamic_pages_control_panel.row_widths", default=[]
        )

        terms = []
        for item in values:
            terms.append(
                SimpleTerm(
                    value=item["row_width_class"],
                    token=str(item["row_width_class"]),
                    title=item["row_width_label"],
                )
            )
        # Create a SimpleVocabulary from the terms list and return it:
        return SimpleVocabulary(terms)


RowWidthFactory = RowWidth()
