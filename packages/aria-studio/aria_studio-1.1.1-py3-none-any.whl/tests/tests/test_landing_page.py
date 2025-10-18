# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

from playwright.sync_api import expect, Page

from tests.pages.landing import LandingPage
from tests.pages.login import LoginPage


def test_links_are_correctly_mapped(page: Page) -> None:
    # Tests the links on landing page
    # Given: The user is logged in
    login_page = LoginPage(page)
    landing_page = LandingPage(page)
    login_page.mock_api()

    # Do: Landing page is opened
    login_page.login_user()

    # Verify: the links are correctly mapped
    expect(landing_page.recordings_on_glasses_link).to_be_visible()
    expect(landing_page.recordings_on_computer_link).to_be_visible()
    expect(landing_page.past_mps_requests_link).to_be_visible()
    expect(landing_page.groups_link).to_be_visible()

    expect(landing_page.ARK_docs_link).to_be_visible()
    expect(landing_page.MPS_docs_link).to_be_visible()
    expect(landing_page.discord_link).to_be_visible()
    expect(landing_page.updates_link).to_be_visible()


# def test_helpful_links_redirection(page: Page) -> None:
#     # Test the redirection of helpful links on landing page

#     # Given: User is logged in and the landing page is opened
#     login_page = LoginPage(page)
#     landing_page = LandingPage(page)

#     login_page.mock_api()
#     login_page.login_user()

#     # Do: click on ARK docs link
#     with page.expect_popup() as popup_info:
#         landing_page.ARK_docs_link.click()
#     ark_docs_page = popup_info.value
#     # Verify: the correct page is opened
#     expect(ark_docs_page.locator("h1")).to_contain_text("Aria Research Kit")

#     # Do: click on MPS docs link
#     with page.expect_popup() as popup_info:
#         landing_page.MPS_docs_link.click()
#     mps_docs_page = popup_info.value
#     # Verify: the correct page is opened
#     expect(mps_docs_page.locator("h1")).to_contain_text(
#         "Project Aria Machine Perception Services"
#     )
#     # Do: click on Discord link
#     with page.expect_popup() as popup_info:
#         landing_page.discord_link.click()
#     discord_page = popup_info.value
#     # Verify: the correct page is opened
#     expect(discord_page).to_have_title("Discord")
