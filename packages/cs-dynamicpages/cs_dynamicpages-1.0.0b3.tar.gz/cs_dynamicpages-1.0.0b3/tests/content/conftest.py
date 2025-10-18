from base64 import b64decode
from collections import defaultdict
from cs_dynamicpages.interfaces import IBrowserLayer
from plone import api
from plone.app.multilingual.interfaces import ITranslationManager
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.namedfile import NamedBlobImage
from plone.testing.zope import Browser
from zope.interface import alsoProvides

import pytest


@pytest.fixture
def contents() -> list:
    """Content to be created."""
    return [
        # EU CONTENT
        {
            "_container": "",
            "_language": "eu",
            "_transitions": ["publish"],
            "type": "Folder",
            "id": "folder",
            "title": "Folder",
        },
        {
            "_container": "folder",
            "_transitions": ["publish"],
            "_language": "eu",
            "type": "DynamicPageFolder",
            "id": "dpf",
            "title": "DPF",
        },
        {
            "_container": "folder/dpf",
            "_transitions": ["publish"],
            "_language": "eu",
            "type": "DynamicPageRow",
            "id": "row-1",
            "title": "Row 1",
        },
        {
            "_container": "folder/dpf",
            "_transitions": ["publish"],
            "_language": "eu",
            "type": "DynamicPageRow",
            "id": "row-2",
            "title": "Row 2",
        },
    ]


@pytest.fixture()
def portal(functional):
    return functional["portal"]


@pytest.fixture()
def browser(functional):
    browser = Browser(functional["app"])
    browser.handleErrors = False
    browser.addHeader("Authorization", f"Basic {SITE_OWNER_NAME}:{SITE_OWNER_PASSWORD}")
    return browser


@pytest.fixture()
def my_request(functional):
    req = functional["request"]
    alsoProvides(req, IBrowserLayer)
    return req


@pytest.fixture
def create_contents(contents):
    """Helper fixture to create initial content."""

    def func(portal) -> dict:
        ids = defaultdict(list)
        for item in contents:
            container_path = item["_container"]
            container = portal.unrestrictedTraverse(container_path)
            payload = {"container": container, "language": item["_language"]}
            if "_image" in item:
                payload["image"] = NamedBlobImage(b64decode(item["_image"]))
            for key, value in item.items():
                if key.startswith("_"):
                    continue
                payload[key] = value

            content = api.content.create(**payload)
            content.language = payload["language"]
            if "_view" in item:
                content.setLayout(item["_view"])
            # Set translation
            if "_translation_of" in item:
                source = portal.unrestrictedTraverse(item["_translation_of"])
                ITranslationManager(source).register_translation(
                    content.language, content
                )
            # Transition items
            if "_transitions" in item:
                transitions = item["_transitions"]
                for transition in transitions:
                    api.content.transition(content, transition=transition)
            ids[container_path].append(content.getId())
        return ids

    return func


@pytest.fixture()
def portal_with_content(app, portal, create_contents):
    """Plone portal with initial content."""
    with api.env.adopt_roles(["Manager"]):
        create_contents(portal)
    # transaction.commit()
    yield portal
    # with api.env.adopt_roles(["Manager"]):
    #     containers = sorted(content_ids.keys(), reverse=True)
    #     for container_path in containers:
    #         container = portal.unrestrictedTraverse(container_path)
    #         container.manage_delObjects(content_ids[container_path])
    # transaction.commit()
