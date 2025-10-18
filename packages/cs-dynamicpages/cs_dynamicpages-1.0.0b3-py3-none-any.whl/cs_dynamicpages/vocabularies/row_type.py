from cs_dynamicpages.content.dynamic_page_row import IDynamicPageRow
from zope.component import getSiteManager
from zope.globalrequest import getRequest
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import providedBy
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class VocabItem:
    def __init__(self, token, value):
        self.token = token
        self.value = value


VIEW_PREFIX = "cs_dynamicpages-"


@implementer(IVocabularyFactory)
class RowType:
    """ """

    def __call__(self, context):
        items = []
        terms = []

        sm = getSiteManager()

        available_views = sm.adapters.lookupAll(
            required=(IDynamicPageRow, providedBy(getRequest())),
            provided=Interface,
        )

        available_view_names = [
            view[0] for view in available_views if view[0].startswith(VIEW_PREFIX)
        ]
        for view_name in available_view_names:
            items.append(VocabItem(view_name, view_name.replace(VIEW_PREFIX, "")))

        for item in items:
            terms.append(
                SimpleTerm(
                    value=item.token,
                    token=str(item.token),
                    title=item.value,
                )
            )
        return SimpleVocabulary(terms)


RowTypeFactory = RowType()
