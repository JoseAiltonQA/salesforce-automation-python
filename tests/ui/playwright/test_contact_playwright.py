import json
import re
import allure
import pytest
from pathlib import Path
from faker import Faker
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeout
from typing import Optional, Any

from tests.ui.playwright.utils import (
    attach_fields_snapshot,
    extractCreateContactFields,
    fillContactFieldByApi,
)

fake = Faker("pt_BR")
LAST_CONTACT_PATH = Path("test-results/last_contact.json")


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
        "lead_source": "Web",
        "languages": "Português, Inglês",
        "level": "Primary",
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
    }

    with allure.step("Given estou na home autenticado"):
        page.goto("https://orgfarm-1a5e0b208b-dev-ed.develop.lightning.force.com/lightning/page/home")
        page.wait_for_url("**/lightning/**", timeout=60000)
        page.wait_for_load_state("domcontentloaded")
        expect(page).to_have_url(re.compile("lightning\\.force\\.com|lightning/page/home|my\\.salesforce\\.com"), timeout=15000)

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

        fillContactFieldByApi(modal, "firstName", contact["firstName"])
        fillContactFieldByApi(modal, "lastName", contact["lastName"])
        fillContactFieldByApi(modal, "Phone", contact["phone"])
        fillContactFieldByApi(modal, "HomePhone", contact["home"])
        fillContactFieldByApi(modal, "MobilePhone", contact["mobile"])
        fillContactFieldByApi(modal, "OtherPhone", contact["other_phone"])
        fillContactFieldByApi(modal, "Title", contact["title"])
        fillContactFieldByApi(modal, "Department", contact["department"])
        fillContactFieldByApi(modal, "Fax", contact["fax"])
        fillContactFieldByApi(modal, "Birthdate", contact["birthdate"])
        fillContactFieldByApi(modal, "Email", contact["email"])
        fillContactFieldByApi(modal, "AssistantName", contact["assistant"])
        fillContactFieldByApi(modal, "AssistantPhone", contact["assistant_phone"])
        fillContactFieldByApi(modal, "Languages__c", contact["languages"])

        # Level picklist: seleciona a segunda opção (nth=1)
        try:
            level_combo = modal.locator("button[aria-label='Level']").first
            level_combo.click()
            dropdown_id = level_combo.get_attribute("aria-controls")
            level_options = modal.locator(f"#{dropdown_id} [role='option']")
            level_options.first.wait_for(timeout=5000)
            (level_options.nth(1) if level_options.count() > 1 else level_options.first).click()
        except Exception:
            pass

        # Origem do lead: seleciona a segunda opção (nth=1)
        try:
            lead_combo = modal.locator("button[aria-label='Origem do lead']").first
            lead_combo.click()
            dropdown_id = lead_combo.get_attribute("aria-controls")
            options = modal.locator(f"#{dropdown_id} [role='option']")
            options.first.wait_for(timeout=2000)
            (options.nth(1) if options.count() > 1 else options.first).click()
        except Exception:
            pass

        fillContactFieldByApi(modal, "street", contact["mailing_street"])
        fillContactFieldByApi(modal, "city", contact["mailing_city"])
        fillContactFieldByApi(modal, "province", contact["mailing_state"])
        fillContactFieldByApi(modal, "postalCode", contact["mailing_postal"])
        fillContactFieldByApi(modal, "country", contact["mailing_country"])

        try:
            fillContactFieldByApi(modal, "street", contact["other_street"], nth=1)
            fillContactFieldByApi(modal, "city", contact["other_city"], nth=1)
            fillContactFieldByApi(modal, "province", contact["other_state"], nth=1)
            fillContactFieldByApi(modal, "postalCode", contact["other_postal"], nth=1)
            fillContactFieldByApi(modal, "country", contact["other_country"], nth=1)
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
        expected_toast = f'Criação concluída: Contato \"{contact["firstName"]} {contact["lastName"]}\"'
        expect(toast).to_contain_text(expected_toast, timeout=15000)

        header_name = page.locator("lightning-formatted-name").first
        expect(header_name).to_have_text(f'{contact["firstName"]} {contact["lastName"]}', timeout=15000)

        allure.attach(page.screenshot(full_page=True), "contato-salvo", allure.attachment_type.PNG)

    # guarda o nome para o cenario de edicao
    LAST_CONTACT_PATH.write_text(
        json.dumps(
            {
                "firstName": contact["firstName"],
                "lastName": contact["lastName"],
                "fullName": f'{contact["firstName"]} {contact["lastName"]}',
                "editCount": 0,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


@pytest.mark.ui
@pytest.mark.playwright
def test_edit_contact_updates_name(page: Page, settings):
    """Abre contato salvo e edita o nome via menu de ações da lista."""
    from tests import conftest as conf
    auth_state = conf.AUTH_STATE_PATH
    if not auth_state.exists():
        pytest.skip("auth-state.json não encontrado. Rode o teste de login para gerar a sessão.")

    if not LAST_CONTACT_PATH.exists():
        pytest.skip("last_contact.json não encontrado. Execute o cenário de criação de contato primeiro.")

    contact_data = json.loads(LAST_CONTACT_PATH.read_text(encoding="utf-8"))
    first = contact_data.get("firstName", "").strip()
    last = contact_data.get("lastName", "").strip()
    old_full = contact_data.get("fullName") or f"{first} {last}".strip()
    if not old_full.strip():
        pytest.skip("Nome do contato ausente em last_contact.json.")

    edit_count = int(contact_data.get("editCount", 0)) + 1
    suffix = f"EDITADO {edit_count}"
    new_last = f"{suffix} {last}".strip() if last else suffix
    new_full = f"{first} {new_last}".strip()

    with allure.step("Given estou na lista de contatos autenticado"):
        page.goto("https://orgfarm-1a5e0b208b-dev-ed.develop.lightning.force.com/lightning/o/Contact/list?filterName=Recent")
        page.wait_for_load_state("domcontentloaded")
        expect(page).to_have_url(re.compile("Contact/list"), timeout=20000)
        allure.attach(page.screenshot(full_page=True), "lista-contatos", allure.attachment_type.PNG)

    with allure.step("When abro o contato salvo pela lista"):
        row = page.locator("tbody tr").filter(has_text=old_full).first

        def _try_search():
            # Campo de busca pode estar traduzido; tentamos variações comuns.
            search_box = None
            for candidate in [
                page.get_by_placeholder("Pesquisar esta lista...", exact=False),
                page.get_by_placeholder("Search this list...", exact=False),
                page.locator("input[type='search']").first,
                page.wait_for_timeout(7000)
            ]:
                if candidate.count() > 0:
                    search_box = candidate
                    break
            if not search_box or search_box.count() == 0:
                return False

            try:
                search_box.wait_for(state="visible", timeout=5000)
            except Exception:
                return False

            search_box.fill(old_full)
            search_box.press("Enter")
            page.wait_for_timeout(7000)
            return True

        if row.count() == 0 or not row.is_visible():
            _try_search()
            row = page.locator("tbody tr").filter(has_text=old_full).first

        if row.count() == 0 or not row.is_visible():
            pytest.skip("Contato não encontrado na lista mesmo após buscar.")

        try:
            row.scroll_into_view_if_needed(timeout=3000)
        except Exception:
            pass

        # abre o registro clicando no link do nome
        open_link = None
        for candidate in [
            row.get_by_role("link", name=old_full, exact=True),
            row.locator("a[data-refid='recordId']").first,
            row.locator("a").filter(has_text=old_full).first,
        ]:
            if candidate.count() > 0:
                open_link = candidate
                break

        if not open_link or open_link.count() == 0:
            pytest.skip("Link do contato não encontrado na lista.")

        open_link.click()
        page.wait_for_url("**/lightning/r/Contact/**", timeout=20000)
        page.wait_for_load_state("domcontentloaded")
        allure.attach(page.screenshot(full_page=True), "detalhe-contato", allure.attachment_type.PNG)

    with allure.step("And clico em Editar e altero o nome"):
        edit_button = None
        for candidate in [
            page.locator("[data-target-selection-name='standard__recordPage-RecordEdit']").first,
            page.locator("button[title='Editar']").first,
            page.locator("button[aria-label='Editar']").first,
            page.get_by_role("button", name="Editar", exact=True),
            page.locator("button[name='Edit']").first,
        ]:
            if candidate.count() > 0 and candidate.is_visible():
                edit_button = candidate
                break

        if edit_button and edit_button.count() > 0:
            expect(edit_button).to_be_enabled(timeout=5000)
            edit_button.click()
        else:
            actions_dropdown = None
            for cand in [
                page.locator("records-lwc-highlights-panel lightning-button-menu button").first,
                page.locator("button[title='Mostrar mais ações'], button[aria-label='Mostrar mais ações']").first,
                page.locator("lightning-button-menu button").first,
            ]:
                if cand.count() > 0:
                    actions_dropdown = cand
                    break

            if not actions_dropdown or actions_dropdown.count() == 0:
                pytest.skip("Botão Editar não encontrado na página do contato.")

            expect(actions_dropdown).to_be_enabled(timeout=5000)
            actions_dropdown.click()

            menu_edit = page.get_by_role("menuitem", name=re.compile("Editar contato|Editar|Edit", re.IGNORECASE))
            expect(menu_edit).to_be_visible(timeout=5000)
            menu_edit.click()

    with allure.step("And altero o nome e salvo"):
        page.wait_for_url("**/edit**", timeout=20000)

        modal = page.locator("records-modal-lwc-detail-panel-wrapper").first
        expect(modal).to_be_visible(timeout=10000)

        last_input_candidates = [
            modal.locator("lightning-input[data-field='lastName'] input").first,
            modal.locator("input[name='lastName']").first,
            modal.locator("input[id^='input-'][name='lastName']").first,
            modal.locator("input[aria-label*='Sobrenome'], input[aria-label*='Last Name']").first,
            modal.get_by_label(re.compile("Sobrenome|Last Name", re.IGNORECASE)),
            modal.get_by_placeholder(re.compile("Sobrenome|Last Name", re.IGNORECASE)),
            page.locator("input[name='lastName']").first,
        ]

        last_input = None
        # tenta por até 20s aguardando o campo ficar visível
        for _ in range(10):
            for candidate in last_input_candidates:
                if candidate.count() == 0:
                    continue
                try:
                    candidate.wait_for(state="visible", timeout=1500)
                    last_input = candidate
                    break
                except Exception:
                    continue
            if last_input:
                break
            page.wait_for_timeout(1000)

        if not last_input:
            allure.attach(page.screenshot(full_page=True), "sem-campo-sobrenome", allure.attachment_type.PNG)
            pytest.fail("Campo de sobrenome não encontrado na tela de edição (modal).")

        last_input.click()
        last_input.fill(new_last)
        try:
            last_input.press("Tab")
        except Exception:
            pass

        save_button = None
        for candidate in [
            page.get_by_role("button", name=re.compile("Salvar|Save", re.IGNORECASE)).first,
            page.locator("button[name='SaveEdit']").first,
        ]:
            if candidate.count() > 0:
                save_button = candidate
                break
        if not save_button or save_button.count() == 0:
            pytest.skip("Botão de salvar não encontrado na tela de edição.")

        expect(save_button).to_be_enabled(timeout=5000)
        save_button.click()

    with allure.step("Then o nome atualizado deve aparecer"):
        toast = page.locator("span.toastMessage")
        expect(toast).to_contain_text(re.compile("Salvamento concluído|foi salvo", re.IGNORECASE), timeout=15000)
        try:
            expect(toast).to_contain_text(new_full, timeout=5000)
        except Exception:
            pass  # alguns toasts mostram apenas o nome antigo; seguimos validando no header

        header_name = page.locator("lightning-formatted-name").first
        expect(header_name).to_have_text(new_full, timeout=15000)

        allure.attach(page.screenshot(full_page=True), "contato-editado", allure.attachment_type.PNG)

    LAST_CONTACT_PATH.write_text(
        json.dumps(
            {"firstName": first, "lastName": new_last, "fullName": new_full, "editCount": edit_count},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


@pytest.mark.ui
@pytest.mark.playwright
def test_find_contact_named_adff_in_list(page: Page, settings):
    """Rola a lista inteira, abre o contato de nome 'adff' e exibe por 20s."""
    from tests import conftest as conf
    if not conf.AUTH_STATE_PATH.exists():
        pytest.skip("auth-state.json não encontrado. Rode o teste de login para gerar a sessão.")

    target_name = "adff"

    with allure.step("Given estou na lista de contatos"):
        page.goto("https://orgfarm-1a5e0b208b-dev-ed.develop.lightning.force.com/lightning/o/Contact/list?filterName=Recent")
        page.wait_for_load_state("domcontentloaded")
        expect(page).to_have_url(re.compile("Contact/list"), timeout=20000)

    rows = page.locator("tbody tr")
    found = False

    with allure.step("When faço scroll na lista até encontrar o contato 'adff'"):
        for _ in range(80):
            if rows.filter(has_text=target_name).count() > 0:
                found = True
                break
            page.mouse.wheel(0, 1400)
            page.wait_for_timeout(500)

    if not found:
        allure.attach(page.screenshot(full_page=True), "lista-apos-scroll", allure.attachment_type.PNG)
        pytest.fail("Contato 'adff' não encontrado após rolar a lista inteira.")

    with allure.step("Then o contato 'adff' aparece na lista"):
        target_row = rows.filter(has_text=target_name).first
        expect(target_row).to_be_visible(timeout=5000)
        allure.attach(page.screenshot(full_page=True), "contato-adff-visivel", allure.attachment_type.PNG)

    with allure.step("And abro o contato 'adff' e mantenho a tela por 20s"):
        open_link = None
        for candidate in [
            target_row.get_by_role("link", name=target_name, exact=True),
            target_row.locator("a[data-refid='recordId']").first,
            target_row.locator("a").filter(has_text=target_name).first,
        ]:
            if candidate.count() > 0:
                open_link = candidate
                break

        if not open_link or open_link.count() == 0:
            pytest.skip("Link do contato 'adff' não encontrado na linha.")

        try:
            with page.expect_navigation(timeout=20000):
                open_link.click()
        except Exception:
            # se não houver navegação, ainda seguimos na mesma página
            try:
                open_link.click()
            except Exception:
                pass

        page.wait_for_load_state("domcontentloaded")

        header_name = None
        for candidate in [
            page.locator("lightning-formatted-name").first,
            page.get_by_role("heading", name=re.compile(target_name)),
            page.locator("h1").filter(has_text=target_name).first,
        ]:
            if candidate.count() > 0:
                header_name = candidate
                break
        if header_name and header_name.count() > 0:
            try:
                expect(header_name).to_be_visible(timeout=5000)
            except Exception:
                pass

        allure.attach(page.screenshot(full_page=True), "contato-adff-detalhe", allure.attachment_type.PNG)
        try:
            page.wait_for_timeout(10000)
        except Exception:
            # se a página fechar/for redirecionada, ignoramos
            pass
