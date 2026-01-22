# Automacao de testes Salesforce (Python + Playwright + Selenium + API)

Guia rapido para rodar e consultar os relatórios (UI e API), com foco em iniciantes.

## O que este projeto faz
- UI: abre a pagina de login do Salesforce e valida campos com Playwright (rapido e estavel) e o mesmo fluxo com Selenium (compatibilidade legada).
- API: consulta o endpoint de limites do Salesforce usando token.
- Relatorios: Allure (HTML navegavel), JUnit/XML, JSON, cobertura e logs sanitizados (sem segredos).

## Requisitos rapidos
- Windows 10+.
- Python 3.10+ (marque "Add Python to PATH" na instalacao).
- Node + npm (para o CLI do Allure).
- Conta Salesforce Developer (gratuita) para usuario/senha/token: https://developer.salesforce.com/signup
- Internet para baixar dependencias e navegador Chromium do Playwright (se for rodar UI).
- Libs extras para dados de teste: `Faker` (gerar dados ficticios) e `validate-docbr` (validar/gerar CPF/CNPJ/telefone de teste) já estao no `requirements.txt`.

## Como preparar o ambiente
1) No PowerShell, entre na pasta do projeto: `cd C:\Estudos\salesforce-automation-python`
2) Crie o ambiente virtual e ative:
   - `python -m venv venv`
   - `.\venv\Scripts\Activate.ps1`
3) Instale dependencias Python:
   - `pip install -r requirements.txt`
4) (Somente UI) Instale navegador do Playwright (uma vez):
   - `python -m playwright install chromium`
5) Crie o `.env` a partir do exemplo:
   - `copy .env.example .env`
   - Preencha: `SF_URL`, `SF_USERNAME`, `SF_PASSWORD`, `SF_TOKEN`, `SF_API_BASE_URL`, `SF_API_VERSION`, `HEADLESS=true|false`
6) Instale o CLI do Allure (para gerar/abrir HTML):
   - Global: `npm install -g allure-commandline@2.30.0 --unsafe-perm`
   - Ou via npx (sem global): prefixe os comandos com `npx allure-commandline@2.30.0 ...`

## Como rodar os testes
- Todos: `pytest`
- Apenas UI Playwright: `pytest -m playwright --headed` (use `HEADLESS=true` no .env para modo oculto)
- Apenas Selenium: `pytest -m selenium`
- Apenas API: `pytest -m api`

## Como gerar e ver relatorios
- Resultados brutos (apos qualquer pytest): `allure-results/`
- Gerar HTML: `allure generate --clean allure-results -o allure-report`
- Abrir HTML local: `allure open allure-report` (ou `allure serve allure-results` para gerar+abrir temporario)
- Artefatos adicionais:
  - JUnit: `reports/junit.xml`
  - JSON: `reports/report.json`
  - Cobertura: `reports/coverage.xml`
  - Logs estruturados de API: `reports/api-logs/*.json` (mascarados)
  - Sumario de saude de API: `reports/api-metrics.{json,txt}`
  - Playwright traces/videos/screenshots: `test-results/` (gerados em toda execucao para UI; videos desde a abertura do navegador ate o fim)
- No Allure, cada teste UI mostra steps (`allure.step`) e anexos (screenshots em cada passo, video completo, trace) mesmo em sucesso.

## Estrutura de pastas
- `config/settings.py` e `config/__init__.py`: carregam .env.
- `tests/conftest.py`: fixtures e hooks (API sanitizer + anexos Allure, Playwright/Selenium, metadados).
- `tests/ui/playwright/test_login_playwright.py`: exemplo Playwright.
- `tests/ui/selenium/test_login_selenium.py`: exemplo Selenium.
- `tests/api/test_limits_api.py`: exemplos de API com steps/labels Allure.
- `.github/workflows/tests.yml`: lint + testes de API + artefatos.

## Segurança e LGPD
- `.env` esta no `.gitignore`; nunca suba segredos.
- Headers sensiveis (Authorization, cookies) e campos sensiveis são mascarados nos logs/anexos.
- PII comum (email/telefone/CPF) e tokens são redigidos nos bodies.
- Use apenas dados de teste/sandbox; evite PII real em ambientes de QA.
- Gere dados ficticios com `Faker` e valide formatos BR (CPF/CNPJ/telefone) com `validate-docbr` em vez de usar dados reais.

## Comandos uteis
- Coleta rapida: `pytest --collect-only`
- Rodar API com cobertura: `pytest -m api`
- Ver trace Playwright: `python -m playwright show-trace test-results/traces/<arquivo>.zip`

## CI (GitHub Actions)
- Workflow `api-tests-and-lint`:
  - Instala deps, roda flake8 em `tests/api` e `config/`, executa `pytest -m api`.
  - Gera Allure HTML no CI e publica artifacts: `allure-results`, `allure-report`, `reports`, `test-results`.
  - Usa apenas secrets (`SF_*`) via variaveis de ambiente; sem segredos em logs.
