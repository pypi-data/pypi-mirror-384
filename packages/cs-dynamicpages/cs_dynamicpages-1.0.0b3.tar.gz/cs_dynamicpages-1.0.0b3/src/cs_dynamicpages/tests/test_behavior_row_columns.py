from cs_dynamicpages.behaviors.row_columns import IRowColumnsMarker
from cs_dynamicpages.testing import CS_DYNAMICPAGES_INTEGRATION_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.behavior.interfaces import IBehavior
from zope.component import getUtility

import unittest


class RowColumnsIntegrationTest(unittest.TestCase):
    layer = CS_DYNAMICPAGES_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    def test_behavior_row_columns(self):
        behavior = getUtility(IBehavior, "cs_dynamicpages.row_columns")
        self.assertEqual(
            behavior.marker,
            IRowColumnsMarker,
        )
