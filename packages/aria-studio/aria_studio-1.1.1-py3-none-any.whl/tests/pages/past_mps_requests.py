# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

from playwright.sync_api import Locator, Page

from tests.utils.constants import PAST_MPS_REQUESTS_URL
from tests.utils.utils import get_mock_data_path, MockDataType


class PastMpsRequestsPage:
    URL: str = PAST_MPS_REQUESTS_URL

    def __init__(self, page: Page) -> None:
        self.page: Page = page
        self.grid_data: Locator = page.get_by_role("grid")

    def navigate(self, url: str = URL) -> None:
        self.page.goto(url)

    def mock_api(self):
        self.page.route(
            "**/mps/get-all-requests/",
            lambda route: route.fulfill(
                path=get_mock_data_path(MockDataType.PAST_MPS_DATA)
            ),
        )
        self.page.route(
            "**/auth/is-logged-in",
            lambda route: route.fulfill(status=200, json=[{"logged_in": True}]),
        )
