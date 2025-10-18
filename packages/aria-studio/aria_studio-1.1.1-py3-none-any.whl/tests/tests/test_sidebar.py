# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

import json

from playwright.sync_api import expect, Page

from tests.pages.login import LoginPage
from tests.pages.sidebar import Sidebar
from tests.utils.utils import get_mock_data_path, MockDataType


def test_device_information(page: Page) -> None:
    # Tests the glasses information rendereing in sidebar

    # Given: the user is logged in
    login_page = LoginPage(page)
    login_page.mock_api()
    login_page.login_user()

    # Do: mock glasses connection
    sidebar = Sidebar(page)
    sidebar.mock_api()
    # Verify: the glasses details are correct
    with open(get_mock_data_path(MockDataType.GLASSES_DATA), "r") as f:
        data = json.load(f)

    expect(sidebar.serial_number).to_contain_text(data["serial_number"])
    expect(sidebar.wifi_battery).to_contain_text(data["wifi_ssid"])
    expect(sidebar.wifi_battery).to_contain_text(str(data["battery_level"]))


def test_glasses_not_connected(page: Page) -> None:
    # Tests the glasses information rendereing in sidebar when glasses are not connected

    # Given: the user is logged in
    login_page = LoginPage(page)
    login_page.mock_api()
    login_page.login_user()

    # Do: Do not mock glasses connection
    sidebar = Sidebar(page)

    # Verify: device not connected is shown
    expect(sidebar.device_not_connected).to_contain_text("Device Not Connected")
