# Sesión 3 · LLM Security Lab

Proyecto práctico de seguridad y arquitectura para aplicaciones que integran modelos de lenguaje (LLM). Incluye una API con FastAPI, una interfaz React, pruebas automatizadas y laboratorios sobre autenticación, protección, disponibilidad, monitoreo, diseño arquitectónico y costos.

## Requisitos

- Python 3.12
- Node.js 22 o superior y npm
- GNU Make
- Docker y Docker Compose (opcional, para ejecutar los servicios en contenedores)

## Estructura del proyecto

```text
.
├── Makefile
├── requirements.txt
├── backend/
│   ├── app/
│   ├── data/
|   |__ Scripts/
│   ├── .env.example
│   └── ...
├── frontend/
│   └── node_modules
│   └── src
│       └── app.jsx
│       └── main.jsx
│   └── ...
└── docs/
|   └── analisi_costos.xlsx
│   └── diagrama C4.pdf
│   └── Documento_de_diseño_RFC.pdf
│   └── Reflexion_critica
└── Makefile
└── Readme.md
└── ...
```

## Instalación inicial

Desde la raíz del repositorio, ejecuta:

```bash
make setup
```

Este comando crea el entorno virtual `.venv` con Python 3.12, , instala las dependencias indicadas en `requirements.txt`, crea `backend/.env` a partir de `backend/.env.example` si todavía no existe e instala las dependencias del frontend con `npm install`.

Si el comando falla porque no se encuentra Python 3.12 o Node.js 22+, instala las versiones requeridas y vuelve a ejecutarlo. Revisa `backend/.env` y ajusta la configuración local antes de iniciar los servicios.

## Ejecución en desarrollo

Abre terminales separadas desde la raíz del proyecto.

**Terminal 1 — backend:**

```bash
make backend
```

La API FastAPI estará disponible en `http://localhost:8000` y la documentación interactiva en `http://localhost:8000/docs`.

**Terminal 2 — frontend:**

```bash
make frontend
```

La interfaz React con Vite estará disponible en `http://localhost:5173`.

Para consultar todos los comandos disponibles:

```bash
make help
```

## Limpieza

Para eliminar cachés de Python, archivos `.pyc`, registros JSONL de `backend/logs/` y la base de datos `backend/llm_security_lab.db`, ejecuta:

```bash
make clean
```

**Importante:** este comando elimina esos registros y esa base de datos locales. Guarda cualquier dato que quieras conservar antes de ejecutarlo.

## Referencia rápida de comandos

| Comando | Descripción |
|---|---|
| `make help` | Muestra la ayuda de los comandos |
| `make setup` | Configura los entornos de backend y frontend |
| `make backend` | Inicia FastAPI en el puerto 8000 |
| `make frontend` | Inicia React/Vite en el puerto 5173 |

## Notas técnicas

- Las recetas de GNU Make se ejecutan en subshells independientes por línea. Por eso, activar el entorno con `source .venv/bin/activate` en una línea no lo mantiene activo en la siguiente. El `Makefile` evita este problema invocando los ejecutables mediante rutas explícitas, como `.venv/bin/python` y `.venv/bin/pytest`.
- Los objetivos `backend`, `frontend` y `test` requieren que primero se complete `make setup`.