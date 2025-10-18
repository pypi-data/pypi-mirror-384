# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from playwright.sync_api import expect, Page
from tests.pages.landing import LandingPage

from tests.pages.login import LoginPage
from tests.pages.sidebar import Sidebar
from tests.utils.constants import LOGIN_URL


def test_mock_login(
    page: Page,
) -> None:
    # Tests the login functionality of the application
    # Given: user is logged out and the login page is opened

    login_page = LoginPage(page)
    login_page.mock_api()

    # Do: fill username and password and click login button
    login_page.login_user()

    # Verify: user is logged in and the sidebar shows logout button
    sidebar = Sidebar(page)
    expect(sidebar.logout_button).to_be_visible()


def test_logout(
    page: Page,
) -> None:
    # Tests the logout functionality of the application
    # Given: user is logged in and the landing page is opened
    login_page = LoginPage(page)
    sidebar = Sidebar(page)
    login_page.mock_api()
    sidebar.mock_api()
    login_page.login_user()
    expect(sidebar.logout_button).to_be_visible()

    # Do: click logout button
    sidebar.click_logout_button()
    # Verify: user is logged in and the sidebar shows logout button
    expect(login_page.login_button).to_be_visible()


def test_nagivation_without_login(
    page: Page,
) -> None:
    # Tests the navigation to pages when user is not logged in

    # Given: user is not logged in
    # user is not logged in by default so no setup needed
    # Do: navigate to landing page
    landing_page = LandingPage(page)
    landing_page.navigate()

    # Verify: user is redirected to login page
    expect(page).to_have_url(LOGIN_URL)
