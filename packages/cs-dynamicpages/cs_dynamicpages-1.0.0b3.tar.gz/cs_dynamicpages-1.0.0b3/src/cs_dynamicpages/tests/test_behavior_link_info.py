from cs_dynamicpages.behaviors.link_info import ILinkInfoMarker
from cs_dynamicpages.testing import CS_DYNAMICPAGES_INTEGRATION_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.behavior.interfaces import IBehavior
from zope.component import getUtility

import unittest


class LinkInfoIntegrationTest(unittest.TestCase):
    layer = CS_DYNAMICPAGES_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    def test_behavior_link_info(self):
        behavior = getUtility(IBehavior, "cs_dynamicpages.link_info")
        self.assertEqual(
            behavior.marker,
            ILinkInfoMarker,
        )
