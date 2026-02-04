import allure
import pytest
from pathlib import Path
from playwright.sync_api import Page, expect


@pytest.mark.ui
@pytest.mark.playwright
def test_user_profile_shows_correct_user(page: Page, settings):
    """Cenário separado para validar o usuário logado via header/profile."""
    from tests import conftest as conf
    auth_state = conf.AUTH_STATE_PATH
    if not auth_state.exists():
        pytest.skip("auth-state.json não encontrado. Rode o teste de login primeiro para gerar o estado.")

    with allure.step("Given estou na home já autenticado"):
        page.goto("https://orgfarm-1a5e0b208b-dev-ed.develop.lightning.force.com/lightning/page/home")
        page.wait_for_url("**/lightning/**", timeout=60000)
        page.wait_for_load_state("domcontentloaded")
        allure.attach(
            page.screenshot(full_page=True),
            name="01-home-authenticated",
            attachment_type=allure.attachment_type.PNG,
        )

    with allure.step("When abro o menu do usuário"):
        profile_button = page.locator(
            "button.branding-userProfile-button, button[title='Exibir painel do usuário'], button[title='User menu']"
        ).first
        expect(profile_button).to_be_visible(timeout=15000)
        profile_button.click()
        allure.attach(
            page.screenshot(full_page=True),
            name="02-profile-menu-opened",
            attachment_type=allure.attachment_type.PNG,
        )

    with allure.step('Then o nome exibido deve ser "José Ailton Junior"'):
        profile_name = page.locator("h1.profile-card-name a.profile-link-label")
        expect(profile_name).to_be_visible()
        expect(profile_name).to_have_text("José Ailton Junior", timeout=10000)
        allure.attach(
            page.screenshot(full_page=True),
            name="03-profile-name-validated",
            attachment_type=allure.attachment_type.PNG,
        )
