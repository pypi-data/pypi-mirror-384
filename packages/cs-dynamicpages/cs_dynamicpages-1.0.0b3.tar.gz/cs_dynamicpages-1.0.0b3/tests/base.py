from cs_dynamicpages import logger
from cs_dynamicpages import PACKAGE_NAME

import pytest


class TestBase:
    @pytest.fixture(autouse=True)
    def installed(self, portal, installer):
        """
        Workaround to test isolation problems when using
        collective.z3cform.datagridfield

        See: https://community.plone.org/t/test-isolation-errors-with-collective-z3cform-datagridfield/7424
        """
        try:
            installer.install_product(PACKAGE_NAME)
        except Exception as e:
            logger.info(e)
            logger.info("Package already installed")
