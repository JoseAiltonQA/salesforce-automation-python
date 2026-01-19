import pytest
from playwright.sync_api import Page


@pytest.mark.ui
@pytest.mark.playwright
def test_login_page_shows_fields(page: Page, settings):
    page.set_default_timeout(10000)
    page.goto(settings.sf_url)

    username = page.wait_for_selector("input#username")
    password = page.wait_for_selector("input#password")
    login_button = page.wait_for_selector("input#Login")

    assert username.is_visible()
    assert password.is_visible()
    assert login_button.is_enabled()


@pytest.mark.ui
@pytest.mark.playwright
def test_can_fill_login_form_with_env_credentials(page: Page, settings):
    if not settings.sf_username or not settings.sf_password:
        pytest.skip("Defina SF_USERNAME e SF_PASSWORD no .env para exercitar o preenchimento do login.")

    page.set_default_timeout(10000)
    page.goto(settings.sf_url)
    page.fill("input#username", settings.sf_username)
    page.fill("input#password", settings.sf_password)
    page.click("input#Login")
    page.wait_for_timeout(3000)

    assert page.url.startswith("https://")
