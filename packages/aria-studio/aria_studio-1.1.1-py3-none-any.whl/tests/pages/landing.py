# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

from playwright.sync_api import Locator, Page
from tests.utils.constants import BASE_URL


class LandingPage:
    URL: str = BASE_URL

    def __init__(self, page: Page) -> None:
        self.page: Page = page

        self.recordings_on_glasses_link: Locator = page.get_by_role(
            "link", name="Recordings on Glasses"
        )
        self.recordings_on_computer_link: Locator = page.get_by_role(
            "link", name="Recordings on computer"
        )
        self.groups_link: Locator = page.get_by_role("link", name="Groups")
        self.past_mps_requests_link: Locator = page.get_by_role(
            "link", name="Past MPS requests"
        )

        self.ARK_docs_link: Locator = page.get_by_test_id("home-link-ark")
        self.MPS_docs_link: Locator = page.get_by_test_id("home-link-mps")
        self.discord_link: Locator = page.get_by_test_id("home-link-discord")
        self.updates_link: Locator = page.get_by_test_id("home-link-updates")

    def navigate(self, url: str = URL) -> None:
        self.page.goto(url)

    def mock_api(self):
        self.page.route(
            "**/auth/is-logged-in",
            lambda route: route.fulfill(status=200, json=[{"logged_in": True}]),
        )
        self.page.route(
            "**/auth/current-user",
            lambda route: route.fulfill(status=200, json=[{"user": "aria_username"}]),
        )
