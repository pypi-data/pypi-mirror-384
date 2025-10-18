from ..base import TestBase
from plone import api

import pytest
import transaction


class TestContent(TestBase):
    @pytest.fixture(autouse=True)
    def create_content(self, portal):
        with api.env.adopt_roles(["Manager"]):
            self.folder = api.content.create(
                container=portal,
                type="Folder",
                id="folder",
            )

            assert self.folder is not None
            assert self.folder.id == "folder"

            self.folder.setLayout("dynamic-view")

            self.dpf = api.content.create(
                container=self.folder, type="DynamicPageFolder", id="dpf", title="DPF"
            )

            assert self.dpf is not None
            assert self.dpf.id == "dpf"

            self.row1 = api.content.create(
                container=self.dpf, type="DynamicPageRow", id="row-1", title="Row 1"
            )
            assert self.row1 is not None
            assert self.row1.id == "row-1"

            self.row2 = api.content.create(
                container=self.dpf, type="DynamicPageRow", id="row-2", title="Row 2"
            )
            assert self.row2 is not None
            assert self.row2.id == "row-2"

            transaction.commit()

    def test_view(self, browser):
        """check that the folder is rendered correctly with the basic instructions"""

        browser.open(self.folder.absolute_url())
        # We have 2 rows, so there must be an option to delete a row
        # assert "Delete row" in browser.contents

        # assert "Row 1" in browser.contents
        # assert "Row 2" in browser.contents

        # There must be an option to add a new row
        assert "Add row" in browser.contents

    # def test_add_row(self, browser):
    #     """click add row"""
    #     browser.open(self.folder.absolute_url())
    #     link = browser.getLink(title="Add row")
    #     link.click()
    #     assert "++add++DynamicPageRow" in browser.url

    #     control = browser.getControl(name="form.widgets.IBasic.title")
    #     control.value = "Row 3"

    #     save = browser.getControl(name="form.buttons.save")
    #     save.click()

    #     browser.open(self.folder.absolute_url())

    #     assert len(self.folder.dpf.keys()) == 3
