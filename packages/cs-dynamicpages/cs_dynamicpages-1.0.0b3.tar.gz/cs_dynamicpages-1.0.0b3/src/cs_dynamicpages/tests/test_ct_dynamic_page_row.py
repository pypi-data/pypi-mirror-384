from cs_dynamicpages.content.dynamic_page_row import IDynamicPageRow
from cs_dynamicpages.testing import CS_DYNAMICPAGES_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import queryUtility

import unittest


class DynamicPageRowIntegrationTest(unittest.TestCase):
    layer = CS_DYNAMICPAGES_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            "DynamicPageFolder",
            self.portal,
            "parent_container",
            title="Parent container",
        )
        self.parent = self.portal[parent_id]

    def test_ct_dynamic_page_row_schema(self):
        fti = queryUtility(IDexterityFTI, name="DynamicPageRow")
        schema = fti.lookupSchema()
        self.assertEqual(IDynamicPageRow, schema)

    def test_ct_dynamic_page_row_fti(self):
        fti = queryUtility(IDexterityFTI, name="DynamicPageRow")
        self.assertTrue(fti)

    def test_ct_dynamic_page_row_factory(self):
        fti = queryUtility(IDexterityFTI, name="DynamicPageRow")
        factory = fti.factory
        obj = createObject(factory)

        self.assertTrue(
            IDynamicPageRow.providedBy(obj),
            f"IDynamicPageRow not provided by {obj}!",
        )

    def test_ct_dynamic_page_row_adding(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        obj = api.content.create(
            container=self.parent,
            type="DynamicPageRow",
            id="dynamic_page_row",
        )

        self.assertTrue(
            IDynamicPageRow.providedBy(obj),
            f"IDynamicPageRow not provided by {obj.id}!",
        )

        parent = obj.__parent__
        self.assertIn("dynamic_page_row", parent.objectIds())

        # check that deleting the object works too
        api.content.delete(obj=obj)
        self.assertNotIn("dynamic_page_row", parent.objectIds())

    def test_ct_dynamic_page_row_globally_not_addable(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="DynamicPageRow")
        self.assertFalse(fti.global_allow, f"{fti.id} is globally addable!")
