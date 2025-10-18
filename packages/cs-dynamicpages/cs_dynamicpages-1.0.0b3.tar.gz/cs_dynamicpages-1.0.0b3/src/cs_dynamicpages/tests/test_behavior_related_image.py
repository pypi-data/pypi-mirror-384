from cs_dynamicpages.behaviors.related_image import IRelatedImageMarker
from cs_dynamicpages.testing import CS_DYNAMICPAGES_INTEGRATION_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.behavior.interfaces import IBehavior
from zope.component import getUtility

import unittest


class RelatedImageIntegrationTest(unittest.TestCase):
    layer = CS_DYNAMICPAGES_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    def test_behavior_related_image(self):
        behavior = getUtility(IBehavior, "cs_dynamicpages.related_image")
        self.assertEqual(
            behavior.marker,
            IRelatedImageMarker,
        )
