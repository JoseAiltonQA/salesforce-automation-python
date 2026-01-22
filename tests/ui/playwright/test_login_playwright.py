import allure
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.ui
@pytest.mark.playwright
def test_login_page_shows_fields(page: Page, settings):
    with allure.step("Given estou na pagina de login"):
        page.set_default_timeout(10000)
        page.goto(settings.sf_url)
        allure.attach(
            page.screenshot(full_page=True),
            name="01-login-page",
            attachment_type=allure.attachment_type.PNG,
        )

    with allure.step("Then os campos de login estao visiveis e habilitados"):
        username = page.locator("input#username")
        password = page.locator("input#password")
        login_button = page.locator("input#Login")

        expect(username).to_be_visible()
        expect(password).to_be_visible()
        expect(login_button).to_be_enabled()
        allure.attach(
            page.screenshot(full_page=True),
            name="02-fields-visible",
            attachment_type=allure.attachment_type.PNG,
        )


@pytest.mark.ui
@pytest.mark.playwright
def test_can_fill_login_form_with_env_credentials(page: Page, settings):
    if not settings.sf_username or not settings.sf_password:
        pytest.skip("Defina SF_USERNAME e SF_PASSWORD no .env")

    with allure.step("Given estou na pagina de login"):
        page.set_default_timeout(10000)
        page.goto(settings.sf_url)
        page.wait_for_timeout(4000)
        allure.attach(
            page.screenshot(full_page=True),
            name="01-login-page",
            attachment_type=allure.attachment_type.PNG,
        )

    with allure.step("When preencho usuario e senha"):
        page.fill("input#username", settings.sf_username)
        page.fill("input#password", settings.sf_password)
        page.wait_for_timeout(3000)
        allure.attach(
            page.screenshot(full_page=True),
            name="02-form-filled",
            attachment_type=allure.attachment_type.PNG,
        )

    with allure.step("And clico em Login"):
        page.click("input#Login")
        page.wait_for_timeout(3000)
        allure.attach(
            page.screenshot(full_page=True),
            name="03-after-click-login",
            attachment_type=allure.attachment_type.PNG,
        )

    with allure.step("Then a URL deve ser https"):
        assert page.url.startswith("https://")
        allure.attach(
            page.screenshot(full_page=True),
            name="04-url-asserted",
            attachment_type=allure.attachment_type.PNG,
        )
