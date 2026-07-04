# Blog Cache API

API для блога с PostgreSQL и Redis-кешированием популярных постов.

## Стек

- Python
- FastAPI
- PostgreSQL
- Redis
- Docker
- Pytest

## Текущий блок

Блок 1: минимальный FastAPI-сервис.

Реализованы endpoint-ы:

- GET /health
- GET /readiness
- GET /version

## Запуск локально

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn[standard]
uvicorn app.main:app --reload