# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

from playwright.sync_api import Locator, Page

from tests.utils.utils import get_mock_data_path, MockDataType


class Sidebar:
    def __init__(self, page: Page) -> None:
        self.page: Page = page
        self.glasses_page_button: Locator = page.get_by_role(
            "button", name="Recordings on glasses"
        )
        self.rec_on_computer_page_button: Locator = page.get_by_role(
            "button", name="Recordings on computer"
        )
        self.past_mps_requests_button: Locator = page.get_by_role(
            "button", name="Past MPS requests"
        )
        self.groups_button: Locator = page.get_by_role("button", name="Groups")
        self.logout_button: Locator = page.get_by_role("button", name="Log out")
        self.serial_number: Locator = page.locator("#root")
        self.wifi_battery: Locator = page.get_by_test_id("content").locator("div")
        self.device_not_connected = page.get_by_test_id("content").get_by_role(
            "paragraph"
        )

    def click_logout_button(self) -> None:
        self.logout_button.click()

    def mock_api(self):
        self.page.route(
            "**/device/status",
            lambda route: route.fulfill(
                path=get_mock_data_path(MockDataType.GLASSES_DATA)
            ),
        )
        self.page.route(
            "**/auth/logout",
            lambda route: route.fulfill(status=200, json=[{"message": "LO200"}]),
        )
