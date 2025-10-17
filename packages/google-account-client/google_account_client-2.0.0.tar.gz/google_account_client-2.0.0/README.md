# 📆 google-account-client

---

# ## DESATUALIZADA ##

---

## 🚀 Instalação

```bash
pip install google-account-client
```

---

## 🔐 Requisitos

- Um arquivo de credenciais do tipo **OAuth Client ID** (`google_app_credentials.json`)
- Um token por usuário (gerado na primeira autenticação)

---

## 🧑‍💻 Primeira autenticação (criando o token)

```python
import datetime as dt
from google_account_client import GoogleAccountFactory

# Factory
google_account_factory = GoogleAccountFactory(credentials_path)

# Cria uma conta Google e dispara o fluxo de login
diacde = google_account_factory.create_account('diacde')

# Salve o token do usuário (preferencia em um arquivo)
with open('user_token', 'w') as token:
    token.write(diacde.get_user_token())
```

---

## 🧪 Exemplo de uso

```python
# Caminho para suas credenciais de app
credentials_path = 'keys/google_app_credentials.json'

# Carregando token de um usuário existente
user_token = 'tokens/user_token.json'

# Instanciando a factory
google_account_factory = GoogleAccountFactory(credentials_path, enable_logs=True)

# Criando uma conta Google conectada
user1 = google_account_factory.create_account('user1', user_token)

# Listando eventos futuros
eventos = user1.calendar_list_events()
for evento in eventos:
    print(evento['summary'])
```

---

## 📅 Criando eventos no Google Calendar

```python
diacde.calendar_create_event(
    summary="Pizza com os devs 🍕",
    start_date_time=dt.datetime(2025, 5, 15, 20, 0),
    end_date_time=dt.datetime(2025, 5, 15, 22, 0),
    location="Rua dos Deploys, 42",
    attendees_emails=["dev@exemplo.com"],
    recurrence_frequency="DAILY",
    recurrence_count=2
)
```

---

## 🔍 Listando eventos

```python
eventos = diacde.calendar_list_events(event_count=5)
for evento in eventos:
    print(f"{evento['summary']} - {evento['start']['dateTime']}")
```

---

## 🧠 Sobre o design

A classe `GoogleAccountFactory` centraliza as credenciais do app, e gerencia instâncias independentes da classe `GoogleAccount`, cada uma representando um usuário autenticado.

---

## 📁 Estrutura mínima de arquivos

```
project/
│
├── keys/
│   └── google_app_credentials.json
│
├── tokens/
│   └── diacde.json
│
└── main.py
```