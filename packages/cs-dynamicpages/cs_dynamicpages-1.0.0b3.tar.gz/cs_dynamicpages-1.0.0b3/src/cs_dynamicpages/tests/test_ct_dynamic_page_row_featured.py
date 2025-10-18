from cs_dynamicpages.content.dynamic_page_row_featured import IDynamicPageRowFeatured
from cs_dynamicpages.testing import CS_DYNAMICPAGES_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import queryUtility

import unittest


class DynamicPageRowFeaturedIntegrationTest(unittest.TestCase):
    layer = CS_DYNAMICPAGES_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            "DynamicPageRow",
            self.portal,
            "parent_container",
            title="Parent container",
        )
        self.parent = self.portal[parent_id]

    def test_ct_dynamic_page_row_featured_schema(self):
        fti = queryUtility(IDexterityFTI, name="DynamicPageRowFeatured")
        schema = fti.lookupSchema()
        self.assertEqual(IDynamicPageRowFeatured, schema)

    def test_ct_dynamic_page_row_featured_fti(self):
        fti = queryUtility(IDexterityFTI, name="DynamicPageRowFeatured")
        self.assertTrue(fti)

    def test_ct_dynamic_page_row_featured_factory(self):
        fti = queryUtility(IDexterityFTI, name="DynamicPageRowFeatured")
        factory = fti.factory
        obj = createObject(factory)

        self.assertTrue(
            IDynamicPageRowFeatured.providedBy(obj),
            f"IDynamicPageRowFeatured not provided by {obj}!",
        )

    def test_ct_dynamic_page_row_featured_adding(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        obj = api.content.create(
            container=self.parent,
            type="DynamicPageRowFeatured",
            id="dynamic_page_row_featured",
        )

        self.assertTrue(
            IDynamicPageRowFeatured.providedBy(obj),
            f"IDynamicPageRowFeatured not provided by {obj.id}!",
        )

        parent = obj.__parent__
        self.assertIn("dynamic_page_row_featured", parent.objectIds())

        # check that deleting the object works too
        api.content.delete(obj=obj)
        self.assertNotIn("dynamic_page_row_featured", parent.objectIds())

    def test_ct_dynamic_page_row_featured_globally_not_addable(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="DynamicPageRowFeatured")
        self.assertFalse(fti.global_allow, f"{fti.id} is globally addable!")
