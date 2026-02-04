import allure
import pytest
import re
from pathlib import Path
from playwright.sync_api import Page, TimeoutError, expect
from tests.utils.logger import step


@pytest.mark.ui
@pytest.mark.playwright
def test_can_fill_login_form_with_env_credentials(page: Page, settings, request):
    if not settings.sf_username or not settings.sf_password:
        pytest.skip("Defina SF_USERNAME e SF_PASSWORD no .env")

    logger = request.node._logger

    with step(logger, "Given estou na pagina de login"):
        page.set_default_timeout(10000)
        page.goto(settings.sf_url)

        #  só continua quando o campo de usuário existir e estiver visível
        username = page.locator("input#username")
        expect(username).to_be_visible()

        allure.attach(
            page.screenshot(full_page=True),
            name="01-login-page",
            attachment_type=allure.attachment_type.PNG,
        )

    with step(logger, "When preencho usuario e senha"):
        password = page.locator("input#password")

        #  garante que os campos estão prontos para digitar
        expect(password).to_be_visible()

        username.fill(settings.sf_username)
        password.fill(settings.sf_password)

        #  valida que os campos realmente ficaram preenchidos
        expect(username).to_have_value(settings.sf_username)
        expect(password).to_have_value(settings.sf_password)

        allure.attach(
            page.screenshot(full_page=True),
            name="02-form-filled",
            attachment_type=allure.attachment_type.PNG,
        )

    with step(logger, "And clico em Login"):
        login_button = page.locator("input#Login")

        #  só clica quando o botão estiver habilitado
        expect(login_button).to_be_enabled()
        login_button.click()

        #  depois do click, esperamos algum “sinal” de próxima etapa.
        #  Fluxo 1: aparece tela de token (input#save)
        #  Fluxo 2: navega direto para o Lightning Home (já autenticado / cookie válido)
        token_seen = False
        try:
            page.wait_for_selector("input#save", timeout=15000)
            token_seen = True
        except TimeoutError:
            pass

        if not token_seen:
            # tenta detectar navegação direta para home/lightning
            try:
                page.wait_for_url("**/lightning/**", timeout=60000)
            except TimeoutError:
                pytest.fail("Não apareceu tela de token nem navegou para o Lightning Home após o login.")

        allure.attach(
            page.screenshot(full_page=True),
            name="03-after-click-login",
            attachment_type=allure.attachment_type.PNG,
        )

    with step(logger, "Then aguardo a validação do token"):
        # Neste ponto podemos estar em dois caminhos:
        # - Token/MFA exibido (input#save visível)
        # - Já navegamos para o Lightning sem token (cookie válido)
        home_url = "**/lightning/page/home"
        current_url = page.url
        if "lightning" in current_url:
            page.wait_for_load_state("domcontentloaded")
        else:
            try:
                page.wait_for_selector("input#save", timeout=1000)
                allure.attach(
                    page.screenshot(full_page=True),
                    name="04-token-page",
                    attachment_type=allure.attachment_type.PNG,
                )
                try:
                    page.wait_for_url(home_url, timeout=180000)
                except TimeoutError:
                    allure.attach(
                        page.screenshot(full_page=True),
                        name="05-token-validation-failed",
                        attachment_type=allure.attachment_type.PNG,
                    )
                    pytest.fail(
                        "Token não validado: a página não navegou para o Lightning Home em até 180s "
                        "após clicar manualmente em 'Verificar'."
                    )
            except TimeoutError:
                # nem token nem lightning, tenta aguardar navegação direta
                page.wait_for_url(home_url, timeout=60000)

    with step(logger, "Then a page do home"):
        #  garante que a navegação terminou e a página carregou o DOM
        page.wait_for_load_state("domcontentloaded")

        #  em vez de assert imediato, o expect espera o título ficar certo
        try:
            expect(page).to_have_title(re.compile("Salesforce", re.IGNORECASE), timeout=30000)
        except Exception:
            # fallback: apenas garante que estamos em lightning/home
            expect(page).to_have_url(re.compile("lightning/page/home"), timeout=30000)

        title = page.title()
        allure.attach(
            title,
            name="page-title",
            attachment_type=allure.attachment_type.TEXT,
        )
        allure.attach(
            page.screenshot(full_page=True),
            name="06-home",
            attachment_type=allure.attachment_type.PNG,
        )

    # Salva o estado autenticado para reutilizar a sessão em outros testes Playwright.
    from tests import conftest as conf

    page.context.storage_state(path=str(conf.AUTH_STATE_PATH))
    allure.attach.file(
        str(conf.AUTH_STATE_PATH),
        name="auth-storage-state",
        attachment_type=allure.attachment_type.JSON,
    )
