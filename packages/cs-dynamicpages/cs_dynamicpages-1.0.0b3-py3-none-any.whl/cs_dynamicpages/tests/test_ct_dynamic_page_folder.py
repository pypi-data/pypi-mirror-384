from cs_dynamicpages.content.dynamic_page_folder import IDynamicPageFolder
from cs_dynamicpages.testing import CS_DYNAMICPAGES_INTEGRATION_TESTING
from plone import api
from plone.api.exc import InvalidParameterError
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import queryUtility

import unittest


class DynamicPageFolderIntegrationTest(unittest.TestCase):
    layer = CS_DYNAMICPAGES_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            "Folder",
            self.portal,
            "parent_container",
            title="Parent container",
        )
        self.parent = self.portal[parent_id]

    def test_ct_dynamic_page_folder_schema(self):
        fti = queryUtility(IDexterityFTI, name="DynamicPageFolder")
        schema = fti.lookupSchema()
        self.assertEqual(IDynamicPageFolder, schema)

    def test_ct_dynamic_page_folder_fti(self):
        fti = queryUtility(IDexterityFTI, name="DynamicPageFolder")
        self.assertTrue(fti)

    def test_ct_dynamic_page_folder_factory(self):
        fti = queryUtility(IDexterityFTI, name="DynamicPageFolder")
        factory = fti.factory
        obj = createObject(factory)

        self.assertTrue(
            IDynamicPageFolder.providedBy(obj),
            f"IDynamicPageFolder not provided by {obj}!",
        )

    def test_ct_dynamic_page_folder_adding(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        obj = api.content.create(
            container=self.parent,
            type="DynamicPageFolder",
            id="dynamic_page_folder",
        )

        self.assertTrue(
            IDynamicPageFolder.providedBy(obj),
            f"IDynamicPageFolder not provided by {obj.id}!",
        )

        parent = obj.__parent__
        self.assertIn("dynamic_page_folder", parent.objectIds())

        # check that deleting the object works too
        api.content.delete(obj=obj)
        self.assertNotIn("dynamic_page_folder", parent.objectIds())

    def test_ct_dynamic_page_folder_globally_not_addable(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="DynamicPageFolder")
        self.assertFalse(fti.global_allow, f"{fti.id} is globally addable!")

    def test_ct_dynamic_page_folder_filter_content_type_true(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="DynamicPageFolder")
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            fti.id,
            self.portal,
            "dynamic_page_folder_id",
            title="DynamicPageFolder container",
        )
        self.parent = self.portal[parent_id]
        with self.assertRaises(InvalidParameterError):
            api.content.create(
                container=self.parent,
                type="Document",
                title="My Content",
            )
