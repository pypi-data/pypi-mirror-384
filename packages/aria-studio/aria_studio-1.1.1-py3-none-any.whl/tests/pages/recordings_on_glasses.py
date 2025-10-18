# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

from playwright.sync_api import Locator, Page

from tests.utils.constants import RECORDINGS_ON_GLASSES_URL
from tests.utils.utils import get_mock_data_path, MockDataType


class RecordingsOnGlassesPage:
    URL: str = RECORDINGS_ON_GLASSES_URL

    def __init__(self, page: Page) -> None:
        self.page: Page = page
        self.grid_view_button: Locator = (
            page.get_by_role("group").get_by_role("button").nth(1)
        )

        self.list_view_button: Locator = (
            page.get_by_role("group").get_by_role("button").first
        )

        self.select_all_button: Locator = page.get_by_role("button", name="Select all")
        self.deselect_all_button: Locator = page.get_by_role(
            "button", name="Deselect all"
        )
        self.grid_data: Locator = page.get_by_role("grid")
        self.device_not_connected_img: Locator = page.get_by_role(
            "img", name="device not connected or no"
        )
        self.no_recordings_on_glasses: Locator = page.get_by_text(
            "No recordings on your glasses"
        )

    def navigate(self, url: str = URL) -> None:
        self.page.goto(url)

    def mock_api(self):
        self.page.route(
            "**/device/list-files?sort_by=start_time&asc=true",
            lambda route: route.fulfill(
                path=get_mock_data_path(MockDataType.GLASSES_FILES)
            ),
        )
        # abort all image requests
        self.page.route(
            "**/device/thumbnail_jpeg/*",
            lambda route: route.abort(),
        )

    def mock_no_files_api(self):
        self.page.route(
            "**/device/list-files?sort_by=start_time&asc=true",
            lambda route: route.fulfill(status=200, json=[{"count": 0, "results": []}]),
        )
