import pytest


@pytest.mark.ui
@pytest.mark.playwright
def test_logging_demo(page, request):
    logger = request.node._logger

    from tests.utils.logger import step

    with step(logger, "Abrindo login"):
        logger.info("Preenchendo usuário", {"user": "masked"})
        page.goto("https://example.com")

    with step(logger, "Validação"):
        logger.warn("Aviso de demonstração", {"detail": "campo opcional"})
        assert page.title() == "Example Domain"
