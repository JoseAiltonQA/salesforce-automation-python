# 📘 Manual Completo — Automação de Testes no Salesforce com Python (Iniciantes Absolutos)

> ⚠️ IMPORTANTE  
> Este projeto foi escrito para **pessoas sem nenhum conhecimento técnico**, começando do **zero absoluto**.  
> Leia com calma e siga os passos **na ordem**. Não pule etapas.

---

## 📌 O que é este projeto?

Este projeto mostra, passo a passo, como **rodar um teste automatizado real** em um sistema chamado Salesforce, usando Python.

Ao executar o projeto, o computador irá:
- Abrir o navegador sozinho
- Acessar o Salesforce
- Digitar usuário e senha
- Fazer login automaticamente

Tudo isso **sem você tocar no mouse**.

---

## 🧠 O que é o Salesforce?

O **Salesforce** é um sistema usado por empresas para gerenciar:
- Clientes
- Vendas
- Contatos
- Processos de negócio

📌 Importante:
- O Salesforce **fica na internet**
- Ele **não é instalado no computador**
- Nós apenas acessamos o site dele automaticamente

---

## 🤖 O que é automação de testes?

Automação de testes é quando:
> O computador executa tarefas sozinho, como se fosse uma pessoa.

Exemplo:
- Abrir um site
- Digitar informações
- Clicar em botões
- Conferir se deu certo

Este projeto faz exatamente isso.

---

# 🪜 PARTE 1 — Preparando o computador

## 1️⃣ Instalar o Python

1. Abra seu navegador (Chrome, Edge, etc)
2. Acesse:  
   https://www.python.org/downloads/
3. Clique em **Download Python**
4. Durante a instalação:
   - ✅ Marque **Add Python to PATH**
5. Finalize a instalação

### ✔️ Verificar se funcionou
1. Pressione **Windows + R**
2. Digite `cmd` e pressione **Enter**
3. Digite:
```bash
python --version
```

Se aparecer algo como:
```
Python 3.x.x
```
👉 Funcionou corretamente.

---

## 2️⃣ Criar uma conta gratuita no Salesforce

1. Acesse:  
   https://developer.salesforce.com/signup
2. Preencha o formulário
3. Confirme o e-mail
4. Guarde:
   - Usuário
   - Senha

⚠️ Você vai precisar disso depois.

---

## 3️⃣ Instalar o Salesforce CLI

Salesforce CLI é um programa que conecta seu computador ao Salesforce.

### Passo a passo:
1. Acesse:  
   https://nodejs.org
2. Baixe e instale (Next, Next, Finish)

Depois:
1. Abra o **CMD**
2. Digite:
```bash
npm install -g @salesforce/cli
```

Verifique:
```bash
sf --version
```

Se aparecer uma versão, está tudo certo.

---

# 🪜 PARTE 2 — Preparando o projeto

## 4️⃣ Criar a pasta do projeto

Crie a pasta:
```
C:\Estudos\salesforce-automation-python
```

Abra o CMD e digite:
```bash
cd C:\Estudos\salesforce-automation-python
```

---

## 5️⃣ Criar o ambiente Python

Digite:
```bash
python -m venv venv
```

Depois:
```bash
venv\Scripts\activate
```

Se aparecer `(venv)` no início da linha, está correto.

---

## 6️⃣ Instalar os programas do projeto

Digite:
```bash
pip install -r requirements.txt
```

Aguarde terminar.

---

# 🪜 PARTE 3 — Configurando dados secretos

## 🔐 O que é o arquivo `.env`?

É um arquivo que guarda:
- Usuário
- Senha

📌 Ele fica **somente no seu computador**  
📌 Ele **não é enviado para a internet**

---

## 7️⃣ Criar o arquivo `.env`

No CMD:
```bash
type nul > .env
```

Agora digite:
```bash
echo SF_URL=https://login.salesforce.com>>.env
echo SF_USERNAME=SEU_USUARIO>>.env
echo SF_PASSWORD=SUA_SENHA>>.env
echo SF_TOKEN=SEU_TOKEN>>.env
```

⚠️ Substitua pelos seus dados reais.

---

# 🪜 PARTE 4 — Entendendo o teste (sem programar)

## 🧩 O que é BDD?

BDD é uma forma de escrever testes como frases normais.

Exemplo:
```
Dado que acesso o Salesforce
Quando faço login
Então vejo a página inicial
```

Você não precisa saber programar para entender isso.

---

## 📂 Estrutura do projeto (explicada)

```
features/
  login.feature      → Texto do teste
steps/
  login_steps.py     → Onde o computador entende o texto
pages/
  login_page.py      → Onde ficam os cliques
```

👉 Neste momento, você **não precisa mexer nesses arquivos**.

---

# ▶️ PARTE 5 — Executando o teste

## 8️⃣ Rodar o teste automatizado

Com `(venv)` ativo, digite:
```bash
behave
```

O que vai acontecer:
1. O navegador abre sozinho
2. O Salesforce é acessado
3. O login é feito automaticamente
4. O teste termina

🎉 Parabéns! Você rodou uma automação real.

---

## ❓ Dúvidas comuns

**Posso quebrar algo?**  
Não. É apenas teste.

**Preciso saber programar agora?**  
Não. Isso vem depois.

**Se der erro, o que faço?**  
Leia o passo novamente e verifique se digitou tudo corretamente.

---

## 🚀 Próximos passos (quando estiver confortável)

- Criar novos testes
- Entender um pouco de Python
- Automatizar outras telas do Salesforce
- Evoluir para testes de API

---

## 👤 Autor

**José Ailton Fernandes Araujo Jr**  
Especialista em Qualidade de Software | QA Automation

Este projeto foi criado com foco em **aprendizado do zero absoluto**.

---

## ⭐ Mensagem Final

Se você conseguiu rodar este projeto:
👉 Você já deu o primeiro passo na automação de testes.

Aprender tecnologia é um processo.  
Errar faz parte.  
Continue.