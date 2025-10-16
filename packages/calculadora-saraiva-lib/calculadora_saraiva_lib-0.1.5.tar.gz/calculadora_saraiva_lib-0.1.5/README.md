# 📟 FastAPI Calculator + Calculator-Lib

Projeto completo usando **Python**, **FastAPI**, **Docker**, **GitHub Packages** e **GitHub Actions**!

---

## 📚 O que esse projeto faz?

- `calculator-lib`: biblioteca Python de operações matemáticas básicas.
- `fastapi-calculator`: serviço FastAPI que usa a calculator-lib para cálculos.
- **CI/CD Automático**: testes → build → publicação no GitHub Packages → build da API → publicação da imagem Docker.

---

## ⚙️ Fluxo de CI/CD (GitHub Actions)

1. Testa a biblioteca `calculator-lib`
2. Publica a biblioteca no GitHub Packages
3. Testa o serviço `fastapi-calculator`
4. Builda e publica o container Docker no GitHub Container Registry (`ghcr.io`)

✅ Cada etapa depende da anterior para garantir a qualidade!

---

## 📦 Instalação local

### 📚 1. Instalar a biblioteca calculator-lib

Se publicada no PyPI ou GitHub Packages:

```bash
pip install calculator-lib
```

Se localmente:

```bash
python -m pip install .
```

---

### 🚀 2. Rodar o serviço FastAPI

Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

Suba a API:

```bash
uvicorn app.main:app --reload
```

Acesse: 👉 http://localhost:8000/docs

---

## 🐳 Rodar usando Docker e Docker Compose

### 📋 Buildar e rodar

```bash
make docker-build     # Builda a imagem usando docker compose
make docker-up        # Sobe o serviço
```

ou em modo detached:

```bash
make docker-up-detached
```

Para derrubar:

```bash
make docker-down
```

Para limpar tudo (imagens, volumes):

```bash
make docker-clean
```

---

## 🛠️ Makefile: Comandos úteis

| Comando | Ação |
|:---|:---|
| `make install` | Instalar dependências da API |
| `make install-lib` | Instalar calculator-lib |
| `make install-dev` | Instalar ferramentas de desenvolvimento |
| `make test-lib` | Testar a biblioteca |
| `make test-app` | Testar a API |
| `make build-lib` | Buildar lib tradicional (`setup.py`) |
| `make build-modern` | Buildar lib moderno (`python -m build`) |
| `make publish-lib` | Publicar lib (quando configurado) |
| `make docker-build` | Buildar imagem Docker via Compose |
| `make docker-up` | Subir serviço Docker |
| `make docker-up-detached` | Subir serviço em background |
| `make docker-down` | Derrubar containers |
| `make docker-clean` | Limpar containers, imagens, volumes |

---

## 📚 Publicação manual da calculator-lib

### 🛠️ Passo a passo

1. Instalar ferramentas de build:

```bash
make install-dev
```

Ou diretamente:

```bash
python -m pip install build twine wheel
```

2. Buildar a lib:

```bash
make build-modern
```
ou

```bash
python -m build
```

Isso vai gerar a pasta `dist/` contendo `.tar.gz` e `.whl`.

3. Publicar no GitHub Packages (ou PyPI)

Se configurado para GitHub Packages:

```bash
python -m twine upload dist/*
```

> Lembre-se de configurar seu `.pypirc` e usar o `GITHUB_TOKEN` ou `TWINE_USERNAME`/`TWINE_PASSWORD`.

---

## 📂 Estrutura do Projeto

```plaintext
fastapi-calculator/
├── app/
│   ├── main.py
│   ├── models.py
├── calculator_lib/
│   ├── __init__.py
│   └── operations.py
├── tests/
│   └── test_main.py
├── tests_lib/
│   └── test_operations.py
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── README.md
├── setup.py
├── pyproject.toml
└── .github/
    └── workflows/
        └── test-and-deploy.yml
```

# testando a lib de novo!!!!!!!