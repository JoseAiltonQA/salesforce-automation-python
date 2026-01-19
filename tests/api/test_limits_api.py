import pytest


@pytest.mark.api
def test_can_read_limits_endpoint(api_client, settings):
    response = api_client.get(f"/services/data/{settings.sf_api_version}/limits")

    assert response.status_code == 200
    data = response.json()
    assert "DailyApiRequests" in data
