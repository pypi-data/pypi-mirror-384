# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.


from playwright.sync_api import expect, Page

from tests.pages.groups import GroupsPage
from tests.pages.login import LoginPage
from tests.pages.sidebar import Sidebar
from tests.utils.utils import generate_random_string


def test_group_creation(page: Page) -> None:
    # Tests the group creation functionality in groups page
    # Given : the groups page is opened

    login_page = LoginPage(page)
    sidebar = Sidebar(page)
    groups_page = GroupsPage(page)

    # Mock the API responses
    login_page.mock_api()
    sidebar.mock_api()
    groups_page.mock_api()

    login_page.login_user()
    expect(sidebar.logout_button).to_be_visible()

    sidebar.groups_button.click()
    # Do: Create a group
    group_name = generate_random_string()
    groups_page.create_group(group_name)
    # Verify: The group is created and the group name is displayed in the table
    expect(groups_page.groups_data).to_contain_text(group_name)
    # Do: Create another group
    group_name_2 = generate_random_string()
    # groups_page.mock_new_group_list_api(group_name_2)
    groups_page.create_group(group_name_2)
    # Verify: The group is created and the group name is displayed in the table
    expect(groups_page.groups_data).to_contain_text(group_name_2)


def test_group_deletion(page: Page) -> None:
    # Tests the group deletion functionality in groups page
    # Given : the groups page is opened
    login_page = LoginPage(page)
    sidebar = Sidebar(page)
    groups_page = GroupsPage(page)

    # Mock the API responses
    login_page.mock_api()
    sidebar.mock_api()
    groups_page.mock_api()

    login_page.login_user()
    expect(sidebar.logout_button, "User should be logged in").to_be_visible()

    sidebar.groups_button.click()
    # Do: Create a group
    group_name = generate_random_string()
    groups_page.create_group(group_name)
    # Verify: The group is created and the group name is displayed in the table
    expect(
        groups_page.groups_data, f"Group {group_name} should be created"
    ).to_contain_text(group_name)
    # Do: Delete the group
    groups_page.delete_group(group_name)
    # Verify: The group is deleted and the group name is not displayed in the table
    expect(
        groups_page.groups_data, f"Group {group_name} should be removed"
    ).not_to_contain_text(group_name)


def test_group_creation_with_duplicate_name(page: Page) -> None:
    # Tests the group name cannot be duplicate
    # Given : the groups page is opened
    login_page = LoginPage(page)
    sidebar = Sidebar(page)
    groups_page = GroupsPage(page)

    # Mock the API responses
    login_page.mock_api()
    sidebar.mock_api()
    groups_page.mock_api()

    login_page.login_user()
    expect(sidebar.logout_button).to_be_visible()
    sidebar.groups_button.click()
    # Do: Create a group
    group_name = generate_random_string()
    groups_page.create_group(group_name)
    # Verify: The group is created and the group name is displayed in the table
    expect(groups_page.groups_data).to_contain_text(group_name)
    # Do: Create another group with same name step by step
    groups_page.mock_delete_api(group_name)
    groups_page.create_new_group_button.click()
    groups_page.new_group_name_input.fill(group_name)
    groups_page.create_modal_button.click()
    # Verify: The group is not created and the error message is displayed
    expect(groups_page.create_modal_button).to_be_disabled()
    expect(groups_page.outlined_error_label_modal).to_be_visible()
    expect(groups_page.outlined_error_label_modal).to_contain_text(
        f"Group '{group_name}' already exists"
    )
