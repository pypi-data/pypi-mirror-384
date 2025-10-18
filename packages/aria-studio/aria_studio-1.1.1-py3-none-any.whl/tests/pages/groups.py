# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

import json
import time

from playwright.sync_api import Locator, Page

from tests.utils.constants import GROUPS_URL
from tests.utils.utils import get_mock_data_path, MockDataType


class GroupsPage:
    URL: str = GROUPS_URL

    def __init__(self, page: Page) -> None:
        self.page: Page = page
        self.create_new_group_button: Locator = page.get_by_role(
            "button", name="Create a new Group"
        )
        self.delete_group_button: Locator = page.get_by_test_id("delete-group-button")
        self.new_group_name_input: Locator = page.get_by_placeholder("New group name")
        self.create_modal_button: Locator = page.get_by_role("button", name="Create")
        self.outlined_error_label_modal: Locator = page.locator("#outlined-error-label")
        self.select_modal_button: Locator = page.get_by_role("button", name="Select")
        self.done_modal_button: Locator = page.get_by_role("button", name="Done")
        self.delete_group_modal_button: Locator = page.get_by_role(
            "button", name="Delete group"
        )
        self.groups_data: Locator = page.locator("tbody")
        self.expand_row: Locator = page.get_by_role("row").get_by_label("expand row")
        self.expand_group_data: Locator = page.get_by_label("purchases")

    def navigate(self, url: str = URL) -> None:
        self.page.goto(url)

    def create_group(self, group_name: str) -> None:
        self.create_new_group_button.click()
        self.new_group_name_input.fill(group_name)
        self.create_modal_button.click()
        self.mock_new_group_list_api(group_name)
        self.select_modal_button.click()
        self.done_modal_button.click()

    def delete_group(self, group_name: str) -> None:
        self.page.unroute("**/group/list")
        self.page.route(
            "**/group/list",
            lambda route: route.fulfill(
                path=get_mock_data_path(MockDataType.GROUP_DATA)
            ),
        )

        self.page.get_by_text(group_name, exact=True).click()
        self.delete_group_button.click()
        self.delete_group_modal_button.click(timeout=10_000)

    def mock_api(self):
        self.page.route("**/group/create", lambda route: route.fulfill(status=200))
        self.page.route("**/group/delete", lambda route: route.fulfill(status=200))
        self.page.route(
            "**/mps/multi/high_level_status", lambda route: route.fulfill(status=200)
        )

        self.page.route(
            "**/group/is_allowed?group_name=*",
            lambda route: route.fulfill(status=200, json={"allowed": True}),
        )
        self.page.route(
            "**/group/list",
            lambda route: route.fulfill(
                path=get_mock_data_path(MockDataType.GROUP_DATA)
            ),
        )

    def mock_new_group_list_api(self, group_name: str):
        """
        This function adds the newly created group to the api response. It is
        done by reading the mock group data from a JSON file,
        appending the new group to the data, and then routing the API to return the updated data.

        Args:
            group_name (str): The name of the new group to be added.

        Returns:
            None
        """
        with open(get_mock_data_path(MockDataType.GROUP_DATA), "r") as f:
            data = json.load(f)
        data.append(
            {
                "name": group_name,
                "path_on_device": f"/home/user/{group_name}",
                "creation_time": int(time.time()),
                "vrs_files": [],
            }
        )
        # remove any existing mocks for this api
        self.page.unroute("**/group/list")
        # mock the api with updated group name
        self.page.route(
            "**/group/list",
            lambda route: route.fulfill(
                json=data,
            ),
        )

    def mock_delete_api(self, group_name: str):
        """
        This function mocks the API response for the delete group functionality.

        It unroutes the existing API route for checking if a group is allowed to be deleted,
        and then routes a new API response that returns a JSON object with a status of 200,
        indicating that the group already exists and cannot be deleted.

        Args:
        group_name (str): The name of the group to be deleted.

        Returns:
        None
        """
        self.page.unroute("**/group/is_allowed?group_name=*")
        self.page.route(
            "**/group/is_allowed?group_name=*",
            lambda route: route.fulfill(
                status=200,
                json={
                    "allowed": False,
                    "detail": f"Group '{group_name}' already exists",
                },
            ),
        )

    def mock_add_files_to_group_api(self, group_name: str):
        """
        This function adds the vrs files to the API response of list groups.

        It unroutes the existing API route,
        and then routes a new API response with new added files to the group.

        Args:
        group_name (str): The name of the group to which files are being added.

        Returns:
        None
        """
        # read the avaialble vrs files from a JSON file
        with open(get_mock_data_path(MockDataType.RECORDINGS_ON_COMPUTER), "r") as f:
            data = json.load(f)
        # create a list of vrs files
        vrs_files = [
            f"{item['file_path']}/{item['file_name']}" for item in data["results"]
        ]

        self.page.unroute("**/group/list")
        self.page.route(
            "**/group/list",
            lambda route: route.fulfill(
                json=[
                    {
                        "name": group_name,
                        "path_on_device": f"/home/user/{group_name}",
                        "creation_time": int(time.time()),
                        "vrs_files": vrs_files,
                    }
                ],
            ),
        )
