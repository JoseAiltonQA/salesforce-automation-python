import json
from typing import Any, Dict, List, Optional

from playwright.sync_api import Locator, Page


def extractCreateContactFields(page: Page) -> List[Dict[str, str]]:
    """
    Varre o modal de criação e retorna [{apiName, label}] para lightning-input-field.
    Útil para debug e ver quais campos estão renderizados na org atual.
    """
    return page.eval_on_selector_all(
        "records-modal-lwc-detail-panel-wrapper lightning-input-field",
        """nodes => nodes
            .map(n => ({
                apiName: n.getAttribute('field-name')
                    || n.getAttribute('data-field-name')
                    || n.getAttribute('data-target-selection-name')
                    || '',
                label: n.getAttribute('data-field-label')
                    || n.getAttribute('aria-label')
                    || n.getAttribute('label')
                    || ''
            }))
            .filter(f => f.apiName)""",
    )


def _fill_text(locator: Locator, value: str) -> None:
    locator.wait_for(state="visible", timeout=10000)
    locator.fill(value)


def fillContactFieldByApi(page: Page, api_name: str, value: str, nth: int = 0) -> None:
    """
    Preenche um campo do modal de contato pelo API name.
    Prioriza inputs/textarea com atributo name e, em seguida,
    procura dentro de lightning-input-field[field-name=...].
    """
    # 1) Busca direta por atributo name.
    input_locator = page.locator(f"[name='{api_name}']")
    if input_locator.count() > nth:
        _fill_text(input_locator.nth(nth), value)
        return

    # 2) Busca dentro de lightning-input-field correspondente.
    wrapper = page.locator(f"lightning-input-field[field-name='{api_name}']")
    if wrapper.count() == 0 or wrapper.count() <= nth:
        raise ValueError(f"Campo {api_name} não encontrado no modal.")

    target = wrapper.nth(nth).locator("input, textarea")
    if target.count() == 0:
        raise ValueError(f"Campo {api_name} não tem input/textarea visível.")
    _fill_text(target.first, value)


def select_combobox_option(modal: Page, button_label: str, option_text: str) -> None:
    """
    Seleciona uma opção em um combobox (lightning-base-combobox) pelo label do botão.
    """
    combo = modal.get_by_role("button", name=button_label)
    combo.click()
    modal.get_by_role("option", name=option_text, exact=True).click()


def pick_first_option_after_type(input_locator: Locator) -> None:
    """
    Digita (ou mantém) o valor atual e escolhe a primeira opção retornada na listbox.
    Útil para lookups lightning.
    """
    input_locator.click()
    options = input_locator.page.get_by_role("option")
    if options.count() == 0:
        raise RuntimeError("Nenhuma opção retornada para o lookup.")
    options.first.click()


def attach_fields_snapshot(allure, fields: List[Dict[str, str]]) -> None:
    allure.attach(
        json.dumps(fields, ensure_ascii=False, indent=2),
        name="contact-fields",
        attachment_type=allure.attachment_type.JSON,
    )
