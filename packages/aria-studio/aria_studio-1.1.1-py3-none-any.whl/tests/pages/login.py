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

from playwright.sync_api import Locator, Page
from tests.utils.constants import ARIA_STUDIO_PASSWORD, ARIA_STUDIO_USERNAME, LOGIN_URL


class LoginPage:
    URL: str = LOGIN_URL

    def __init__(self, page: Page) -> None:
        self.page: Page = page
        self.login_button: Locator = page.get_by_role("button", name="Login")

    def navigate(self, url: str = URL) -> None:
        self.page.goto(url)

    def fill_username(self, username: str) -> None:
        self.page.locator('input[name="username"]').fill(username)

    def fill_password(self, password: str) -> None:
        self.page.locator('input[name="password"]').fill(password)

    def click_login_button(self) -> None:
        self.login_button.click()

    def login_user(self):
        self.navigate(self.URL)
        self.fill_username(ARIA_STUDIO_USERNAME)
        self.fill_password(ARIA_STUDIO_PASSWORD)
        self.click_login_button()

    def mock_api(self):
        self.page.route(
            "**/auth/current-user",
            lambda route: route.fulfill(status=200, json=[{"user": "aria_username"}]),
        )
        self.page.route(
            "**/auth/is-logged-in",
            lambda route: route.fulfill(status=200, json=[{"logged_in": True}]),
        )
        self.page.route(
            "**/auth/login",
            lambda route: route.fulfill(
                status=200, json=[{"message": "Logged in successfully"}]
            ),
        )
