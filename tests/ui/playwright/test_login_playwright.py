import allure
import pytest
from playwright.sync_api import Page, TimeoutError, expect


@pytest.mark.ui
@pytest.mark.playwright
def test_can_fill_login_form_with_env_credentials(page: Page, settings):
    if not settings.sf_username or not settings.sf_password:
        pytest.skip("Defina SF_USERNAME e SF_PASSWORD no .env")

    with allure.step("Given estou na pagina de login"):
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

    with allure.step("When preencho usuario e senha"):
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

    with allure.step("And clico em Login"):
        login_button = page.locator("input#Login")

        #  só clica quando o botão estiver habilitado
        expect(login_button).to_be_enabled()
        login_button.click()

        #  depois do click, esperamos algum “sinal” de próxima etapa.
        # Aqui, o sinal é: aparecer o elemento da página de token (input#save)
        page.wait_for_selector("input#save", timeout=120000)

        allure.attach(
            page.screenshot(full_page=True),
            name="03-after-click-login",
            attachment_type=allure.attachment_type.PNG,
        )

    with allure.step("Then aguardo a validação do token"):
        # Neste ponto a tela de token já apareceu (porque esperamos por input#save acima)
        allure.attach(
            page.screenshot(full_page=True),
            name="04-token-page",
            attachment_type=allure.attachment_type.PNG,
        )

        # Só continua quando o usuário clicar manualmente em "Verificar"
        try:
            page.wait_for_url(
                "**/lightning/page/home", 
                timeout=180000
                )
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
        else:
            allure.attach(
                page.screenshot(full_page=True),
                name="05-token-validated",
                attachment_type=allure.attachment_type.PNG,
            )

    with allure.step("Then a page do home"):
        #  garante que a navegação terminou e a página carregou o DOM
        page.wait_for_load_state("domcontentloaded")

        #  em vez de assert imediato, o expect espera o título ficar certo
        expect(page).to_have_title("Início | Salesforce")

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
