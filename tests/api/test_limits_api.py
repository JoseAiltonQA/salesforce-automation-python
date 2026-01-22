import allure
import pytest


@allure.feature("API Limits")
@allure.story("Consultar limites da organizacao")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_can_read_limits_endpoint(api_client, settings):
    with allure.step("When consulto o endpoint de limites"):
        response = api_client.get(f"/services/data/{settings.sf_api_version}/limits")

    with allure.step("Then o status deve ser 200"):
        assert response.status_code == 200

    with allure.step("And deve conter a chave DailyApiRequests"):
        data = response.json()
        assert "DailyApiRequests" in data
        assert data["DailyApiRequests"]["Max"] > 0


@allure.feature("API Limits")
@allure.story("Validar contrato basico")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.api
def test_limits_endpoint_has_expected_fields(api_client, settings):
    with allure.step("When consulto o endpoint de limites"):
        response = api_client.get(f"/services/data/{settings.sf_api_version}/limits")

    with allure.step("Then o status deve ser 200"):
        assert response.status_code == 200

    with allure.step("And o payload contem campos essenciais"):
        payload = response.json()
        expected_keys = {"DailyApiRequests", "DataStorageMB", "FileStorageMB"}
        assert expected_keys.issubset(set(payload.keys()))
