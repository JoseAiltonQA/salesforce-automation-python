import pytest
from selenium.webdriver.common.by import By


@pytest.mark.ui
@pytest.mark.selenium
def test_login_page_loads_and_has_fields(selenium_driver, settings):
    selenium_driver.get(settings.sf_url)

    assert "Salesforce" in selenium_driver.title
    assert selenium_driver.find_element(By.ID, "username")
    assert selenium_driver.find_element(By.ID, "password")
    assert selenium_driver.find_element(By.ID, "Login")


@pytest.mark.ui
@pytest.mark.selenium
def test_can_fill_login_form_with_env_credentials(selenium_driver, settings):
    if not settings.sf_username or not settings.sf_password:
        pytest.skip("Defina SF_USERNAME e SF_PASSWORD no .env para exercitar o preenchimento do login.")

    selenium_driver.get(settings.sf_url)
    selenium_driver.find_element(By.ID, "username").send_keys(settings.sf_username)
    selenium_driver.find_element(By.ID, "password").send_keys(settings.sf_password)
    selenium_driver.find_element(By.ID, "Login").click()

    assert selenium_driver.current_url.startswith("https://")
