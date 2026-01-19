<<<<<<< HEAD
# salesforce-automation-python
Este projeto mostra, passo a passo, como **rodar um teste automatizado real** em um sistema Salesforce, usando Python.
=======
# Automacao de testes Salesforce (Python + Playwright + Selenium + API)

Este guia foi escrito para quem nunca programou. Basta seguir na ordem.

## O que este projeto faz
- Abre a pagina de login do Salesforce e valida campos com Playwright (rapido e estavel).
- Mostra o mesmo fluxo com Selenium (para quem precisa de compatibilidade legada).
- Faz uma chamada REST para o endpoint de limites do Salesforce usando um token.
- Todas as variaveis ficam no seu computador (.env) e nao sao enviadas para a internet.

## Requisitos rapidos
- Windows 10 ou mais recente.
- Python 3.10 ou mais recente (marque "Add Python to PATH" na instalacao).
- Conta Salesforce Developer (gratis) para ter usuario, senha e token: https://developer.salesforce.com/signup
- Internet liberada para baixar as dependencias e o navegador Chromium do Playwright.

## Passo a passo (iniciante)
1) Baixe ou clone o projeto e abra o PowerShell na pasta `C:\Estudos\salesforce-automation-python`.
2) Crie o ambiente virtual:
   - `python -m venv venv`
   - Ative: `.\venv\Scripts\Activate.ps1` (o prompt vai mostrar `(venv)`).
3) Instale as dependencias:
   - `pip install -r requirements.txt`
4) Baixe o navegador usado pelo Playwright (roda uma vez):
   - `python -m playwright install chromium`
5) Crie o arquivo `.env` com suas credenciais (fica so na sua maquina):
   - `copy .env.example .env`
   - Abra `.env` e preencha:
     - `SF_URL` = url de login, exemplo `https://login.salesforce.com`
     - `SF_USERNAME` = seu usuario do Salesforce
     - `SF_PASSWORD` = sua senha do Salesforce
     - `SF_TOKEN` = token de acesso (Bearer). Pode vir de uma Connected App ou do seu processo de integracao.
     - `SF_API_BASE_URL` = dominio da sua org, exemplo `https://sua-instancia.my.salesforce.com`
     - `SF_API_VERSION` = versao da API, exemplo `v61.0`
     - `HEADLESS` = `true` para rodar sem abrir janela, `false` para ver a navegacao do Selenium
6) Teste se tudo esta instalado:
   - `pytest --collect-only` (so coleta, nao executa nada pesado)

## Como rodar os testes
- Todos os testes: `pytest`
- Somente Playwright: `pytest -m playwright --headed` (use `--headed` para ver o navegador; sem isso roda em modo oculto)
- Somente Selenium: `pytest -m selenium`
- Somente API: `pytest -m api`
- Para rodar de forma silenciosa, deixe `HEADLESS=true` no `.env`.

## Estrutura de pastas que voce vai usar
- `config/settings.py` carrega as variaveis do `.env`.
- `tests/conftest.py` configura fixtures compartilhadas (Playwright, Selenium, API).
- `tests/ui/playwright/test_login_playwright.py` valida a pagina de login com Playwright.
- `tests/ui/selenium/test_login_selenium.py` faz o mesmo com Selenium.
- `tests/api/test_limits_api.py` chama o endpoint de limites do Salesforce (usa o token).
- `.env.example` mostra o formato correto do `.env` (copie e preencha).

## Notas importantes sobre o Salesforce
- Use `SF_API_BASE_URL` igual ao dominio da sua org, nao o de login. Exemplo: depois que voce faz login, copie o inicio da URL antes do `/lightning`.
- O token (`SF_TOKEN`) precisa ter permissao para acessar a API REST. Sem isso o teste de API retorna 401.
- Os testes de UI pulam automaticamente se usuario ou senha nao estiverem preenchidos. O teste de API pula se faltar base URL ou token.

## Erros comuns e como resolver
- `python nao reconhecido`: reinstale o Python marcando "Add Python to PATH".
- `ModuleNotFoundError` ou falha no `pip`: verifique se o ambiente virtual esta ativo (`(venv)` no prompt) e tente `pip install -r requirements.txt` de novo.
- `playwright install` falhou: confira se ha internet e rode o comando novamente.
- API retornou 401/403: confirme `SF_TOKEN`, o dominio em `SF_API_BASE_URL` e se o usuario tem permissao de API.

## Sugestoes
- VSCode: instale as extensoes recomendadas (Python, Pylance, Playwright, Salesforce DX, ESLint e Prettier). O arquivo `.vscode/extensions.json` ja sugere todas.
- Para ver os testes Playwright de forma visual, rode `pytest -m playwright --headed`.
- Quando for criar cenarios novos, siga o padrao: settings no `.env`, fixtures em `tests/conftest.py` e testes em `tests/ui` ou `tests/api`.

## Proximos passos (quando estiver confortavel)
- Adicionar novos cenarios de UI na pasta `tests/ui`.
- Cobrir fluxos de negocio especificos criando novas funcoes de Page Object.
- Criar testes de API adicionais (ex.: CRUD de objetos) reaproveitando o `api_client`.
>>>>>>> 9a8b760 (Configuração inicial do projeto, com o apio do ChatGPT e regras criadas especificas para o uso de IA)
