import allure
import pytest
from pathlib import Path
from faker import Faker
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeout

from tests.ui.playwright.utils import (
    attach_fields_snapshot,
    extractCreateContactFields,
    fillContactFieldByApi,
)

fake = Faker("pt_BR")


@pytest.mark.ui
@pytest.mark.playwright
def test_create_contact_full_form(page: Page, settings):
    """Cria um contato preenchendo campos obrigatórios e opcionais."""
    from tests import conftest as conf
    auth_state = conf.AUTH_STATE_PATH
    if not auth_state.exists():
        pytest.skip("auth-state.json não encontrado. Rode o teste de login para gerar a sessão.")

    contact = {
        "salutation": "Sr.",
        "firstName": fake.first_name(),
        "lastName": fake.last_name(),
        "phone": fake.phone_number(),
        "mobile": fake.phone_number(),
        "home": fake.phone_number(),
        "other_phone": fake.phone_number(),
        "title": fake.job(),
        "department": "Vendas",
        "fax": fake.msisdn()[0:10],
        "birthdate": fake.date_of_birth(minimum_age=25, maximum_age=50).strftime("%d/%m/%Y"),
        "email": fake.email(),
        "assistant": fake.name(),
        "assistant_phone": fake.phone_number(),
        "lead_source": None,
        "languages": "Português, Inglês",
        "level": None,
        "description": fake.text(max_nb_chars=120),
        "mailing_street": fake.street_address(),
        "mailing_city": fake.city(),
        "mailing_state": "SP",
        "mailing_postal": fake.postcode(),
        "mailing_country": "Brasil",
        "other_street": fake.street_address(),
        "other_city": fake.city(),
        "other_state": "SP",
        "other_postal": fake.postcode(),
        "other_country": "Brasil",
        "account_lookup": "Conta",
        "reports_to_lookup": "José",
    }

    with allure.step("Given estou na home autenticado"):
        page.goto("https://orgfarm-1a5e0b208b-dev-ed.develop.lightning.force.com/lightning/page/home")
        page.wait_for_load_state("domcontentloaded")
        expect(page).to_have_url("https://orgfarm-1a5e0b208b-dev-ed.develop.lightning.force.com/lightning/page/home")

    with allure.step("When abro o menu e clico em Novo contato"):
        menu_icon = page.locator("one-app-nav-bar-menu-button a[role='button']").filter(
            has_text="Contatos Lista"
        )
        menu_icon.click()
        novo_contato = page.get_by_role("menuitem", name="Novo contato")
        novo_contato.wait_for(timeout=3000)
        novo_contato.click()

    with allure.step("Then o modal de Criar contato deve aparecer"):
        modal = page.locator("records-modal-lwc-detail-panel-wrapper").first
        header = modal.get_by_role("heading", name="Criar contato")
        header.wait_for(timeout=15000)
        expect(header).to_be_visible()
        allure.attach(page.screenshot(full_page=True), "modal-criar-contato", allure.attachment_type.PNG)

    with allure.step("And mapeio os campos disponíveis"):
        fields = extractCreateContactFields(page)
        attach_fields_snapshot(allure, fields)

    with allure.step("And preencho o formulário completo"):
        try:
            salutation = modal.get_by_role("button", name="Tratamento")
            salutation.click()
            modal.get_by_role("option", name=contact["salutation"]).click()
        except PlaywrightTimeout:
            pass

        fillContactFieldByApi(modal, "firstName", contact["firstName"], timeout=2000)
        fillContactFieldByApi(modal, "lastName", contact["lastName"], timeout=2000)
        fillContactFieldByApi(modal, "Phone", contact["phone"], timeout=2000)
        fillContactFieldByApi(modal, "HomePhone", contact["home"], timeout=2000)
        fillContactFieldByApi(modal, "MobilePhone", contact["mobile"], timeout=2000)
        fillContactFieldByApi(modal, "OtherPhone", contact["other_phone"], timeout=2000)
        fillContactFieldByApi(modal, "Title", contact["title"], timeout=2000)
        fillContactFieldByApi(modal, "Department", contact["department"], timeout=2000)
        fillContactFieldByApi(modal, "Fax", contact["fax"], timeout=2000)
        fillContactFieldByApi(modal, "Birthdate", contact["birthdate"], timeout=2000)
        fillContactFieldByApi(modal, "Email", contact["email"], timeout=2000)
        fillContactFieldByApi(modal, "AssistantName", contact["assistant"], timeout=2000)
        fillContactFieldByApi(modal, "AssistantPhone", contact["assistant_phone"], timeout=2000)
        fillContactFieldByApi(modal, "Languages__c", contact["languages"], timeout=2000)

        try:
            level_combo = modal.get_by_role("button", name="Level")
            level_combo.click()
            options = modal.get_by_role("option")
            for i in range(options.count()):
                if "--Nenhum--" not in options.nth(i).inner_text():
                    options.nth(i).click()
                    break
        except Exception:
            pass

        fillContactFieldByApi(modal, "street", contact["mailing_street"], timeout=2000)
        fillContactFieldByApi(modal, "city", contact["mailing_city"], timeout=2000)
        fillContactFieldByApi(modal, "province", contact["mailing_state"], timeout=2000)
        fillContactFieldByApi(modal, "postalCode", contact["mailing_postal"], timeout=2000)
        fillContactFieldByApi(modal, "country", contact["mailing_country"], timeout=2000)

        try:
            fillContactFieldByApi(modal, "street", contact["other_street"], nth=1, timeout=1500)
            fillContactFieldByApi(modal, "city", contact["other_city"], nth=1, timeout=1500)
            fillContactFieldByApi(modal, "province", contact["other_state"], nth=1, timeout=1500)
            fillContactFieldByApi(modal, "postalCode", contact["other_postal"], nth=1, timeout=1500)
            fillContactFieldByApi(modal, "country", contact["other_country"], nth=1, timeout=1500)
        except PlaywrightTimeout:
            pass

        modal.get_by_label("Descrição").fill(contact["description"])

        allure.attach(page.screenshot(full_page=True), "form-preenchido", allure.attachment_type.PNG)

    with allure.step("And salvo o contato"):
        save_button = modal.locator("li[data-target-selection-name='sfdc:StandardButton.Contact.SaveEdit'] button[name='SaveEdit']").first
        expect(save_button).to_be_enabled(timeout=5000)
        save_button.click()

    with allure.step("Then devo ver a criação concluída"):
        toast = page.locator("span.toastMessage")
        expected_toast = f'Criação concluída: Contato "{contact["firstName"]} {contact["lastName"]}"'
        expect(toast).to_contain_text(expected_toast, timeout=15000)

        header_name = page.locator("lightning-formatted-name").first
        expect(header_name).to_have_text(f'{contact["firstName"]} {contact["lastName"]}', timeout=15000)

        allure.attach(page.screenshot(full_page=True), "contato-salvo", allure.attachment_type.PNG)
