import httpx
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config.settings import get_settings


@pytest.fixture(scope="session")
def settings():
    return get_settings()


@pytest.fixture(scope="session")
def api_client(settings):
    if not settings.sf_api_base_url or not settings.sf_token:
        pytest.skip("Defina SF_API_BASE_URL e SF_TOKEN no .env para rodar testes de API.")

    headers = {
        "Authorization": f"Bearer {settings.sf_token}",
        "Content-Type": "application/json",
    }

    return httpx.Client(base_url=settings.sf_api_base_url, headers=headers, timeout=30.0)


@pytest.fixture()
def selenium_driver(settings):
    options = Options()
    if settings.headless:
        options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    yield driver
    driver.quit()
