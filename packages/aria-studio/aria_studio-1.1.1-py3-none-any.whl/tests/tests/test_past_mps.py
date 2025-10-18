# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

import json

from playwright.sync_api import expect, Page

from tests.pages.login import LoginPage
from tests.pages.past_mps_requests import PastMpsRequestsPage
from tests.pages.sidebar import Sidebar
from tests.utils.utils import get_mock_data_path, MockDataType


def test_past_mps_data(page: Page) -> None:
    # Tests the Past mps page contains a grid with all past MPS requests

    # Given: User is logged in and user has past MPS requests
    login_page = LoginPage(page)
    sidebar = Sidebar(page)
    past_mps_requests_page = PastMpsRequestsPage(page)
    # Mock the API response
    login_page.mock_api()
    past_mps_requests_page.mock_api()

    login_page.login_user()
    expect(sidebar.logout_button).to_be_visible()

    # Do: Past mps requests page is opened
    sidebar.past_mps_requests_button.click()

    # Verify: The grid contains all past MPS requests and their details
    with open(get_mock_data_path(MockDataType.PAST_MPS_DATA), "r") as f:
        data = json.load(f)

    file1 = data["requests"][0]
    file2 = data["requests"][1]
    file3 = data["requests"][2]
    expect(past_mps_requests_page.grid_data).to_contain_text(file1["name"])
    expect(past_mps_requests_page.grid_data).to_contain_text(file2["name"])
    expect(past_mps_requests_page.grid_data).to_contain_text(file3["name"])
