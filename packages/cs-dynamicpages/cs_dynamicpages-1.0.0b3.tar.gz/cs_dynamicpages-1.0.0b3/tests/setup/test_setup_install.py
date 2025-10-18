from ..base import TestBase
from cs_dynamicpages import PACKAGE_NAME


class TestSetupInstall(TestBase):
    def test_addon_installed(self, installer):
        """Test if cs_dynamicpages is installed."""
        assert installer.is_product_installed(PACKAGE_NAME) is True

    def test_browserlayer(self, browser_layers):
        """Test that IBrowserLayer is registered."""
        from cs_dynamicpages.interfaces import IBrowserLayer

        assert IBrowserLayer in browser_layers

    def test_latest_version(self, profile_last_version):
        """Test latest version of default profile."""
        assert profile_last_version(f"{PACKAGE_NAME}:default") == "1005"
