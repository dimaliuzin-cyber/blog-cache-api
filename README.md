# API для блога с кешированием популярных постов

REST API для управления постами блога с поддержкой Redis-кеширования часто запрашиваемых данных.

Проект выполнен в рамках тестового задания **«Вариант Б. Проектирование системы с кешированием»**.

Основная задача проекта — показать, как можно построить небольшой backend-сервис, в котором основная база данных и кеш работают вместе, но выполняют разные роли.

**PostgreSQL** используется как основной источник актуальных данных. В нем хранятся посты и выполняются операции создания, обновления и удаления.

**Redis** используется как быстрый временный кеш для повторного чтения постов. При запросе `GET /posts/{post_id}` сервис сначала проверяет наличие записи в Redis. Если запись найдена, данные возвращаются из кеша. Если записи нет, сервис загружает пост из PostgreSQL, сохраняет его в Redis с TTL и возвращает клиенту.

При обновлении или удалении поста соответствующая запись в кеше инвалидируется. Благодаря этому следующий запрос получает актуальные данные из PostgreSQL, а не устаревшую версию из Redis.

Проект включает:

- REST API на FastAPI;
- PostgreSQL как основное хранилище данных;
- Redis-кеширование по паттерну `cache-aside`;
- миграции базы данных через Alembic;
- Docker Compose для запуска всего окружения;
- единый формат ошибок;
- request id для трассировки запросов;
- логирование ключевых операций;
- unit- и integration-тесты, включая проверку логики кеширования.

---

## Содержание

- [1. Краткое описание](#1-краткое-описание)
- [2. Что реализовано](#2-что-реализовано)
- [3. Стек технологий](#3-стек-технологий)
- [4. Архитектура](#4-архитектура)
- [5. Переменные окружения](#5-переменные-окружения)
- [6. Запуск через Docker Compose](#6-запуск-через-docker-compose)
- [7. Миграции базы данных](#7-миграции-базы-данных)
- [8. API endpoints](#8-api-endpoints)
- [9. Кеширование](#9-кеширование)
- [10. Логирование и Request ID](#10-логирование-и-request-id)
- [11. Тестирование](#11-тестирование)
- [12. Соответствие требованиям задания](#12-соответствие-требованиям-задания)

---

## 1. Краткое описание

Проект показывает реализацию небольшого backend-сервиса, в котором обычный CRUD API дополнен кешированием чтения через Redis.

Основной акцент сделан не на количестве endpoints, а на корректной организации backend-приложения:

- бизнес-логика вынесена в отдельный service layer;
- работа с PostgreSQL изолирована в repository layer;
- взаимодействие с Redis вынесено в отдельный cache layer;
- HTTP-слой не содержит прямой работы с базой данных или кешем;
- настройки приложения загружаются из `.env`;
- схема базы данных управляется через Alembic;
- поведение API и кеширования покрыто автоматическими тестами.

Такой подход делает код проще для проверки, расширения и сопровождения. Например, логику кеширования можно изменить внутри `posts/cache.py` и `posts/service.py`, не переписывая HTTP endpoints. А работу с PostgreSQL можно развивать в репозитории, не смешивая SQLAlchemy-код с FastAPI-роутерами.

Проект также демонстрирует базовые практики, которые важны для production-подхода:

- явное разделение ответственности между слоями;
- единый формат ошибок;
- трассировку запросов через `X-Request-ID`;
- логирование ключевых операций;
- контейнеризированный запуск окружения;
- воспроизводимую проверку через тесты и команды, приведенные ниже, в этом файле.
---

## 2. Что реализовано

В проекте реализованы основные возможности, необходимые для системы с кешированием:

- создание поста;
- получение поста по `id`;
- частичное обновление поста;
- удаление поста;
- чтение поста из Redis при повторном запросе;
- загрузка поста из PostgreSQL при отсутствии записи в кеше;
- сохранение поста в Redis с TTL;
- инвалидация кеша при обновлении поста;
- инвалидация кеша при удалении поста;
- единый формат ошибок;
- middleware для `X-Request-ID`;
- логирование ключевых операций;
- настройки через `.env`;
- Docker Compose окружение с API, PostgreSQL и Redis;
- миграции Alembic;
- unit-тесты сервисного слоя;
- интеграционные тесты API;
- интеграционные тесты логики кеширования.

---

## 3. Стек технологий

| Компонент | Назначение |
|---|---|
| Python 3.13 | Основной язык разработки |
| FastAPI | REST API и OpenAPI-документация |
| Pydantic v2 | Валидация входных и выходных данных |
| pydantic-settings | Загрузка настроек из `.env` |
| PostgreSQL | Основное хранилище данных |
| SQLAlchemy Async ORM | Асинхронная работа с PostgreSQL |
| Alembic | Управление миграциями базы данных |
| Redis | Кеширование часто запрашиваемых постов |
| redis.asyncio | Асинхронный Redis-клиент |
| Docker | Контейнеризация приложения |
| Docker Compose | Запуск API, PostgreSQL и Redis |
| Pytest | Автоматическое тестирование |
| pytest-asyncio | Поддержка асинхронных тестов |
| HTTPX | Интеграционное тестирование HTTP API |
| Ruff | Линтинг и форматирование кода |

---

## 4. Архитектура

Проект построен по принципу разделения ответственности между слоями приложения.

Главная идея архитектуры — не смешивать HTTP-логику, бизнес-правила, работу с базой данных и работу с кешем в одном месте. Благодаря этому код проще читать, тестировать и расширять.

### Основные слои приложения

| Слой | Ответственность |
|---|---|
| `api/routers` | Принимает HTTP-запросы, вызывает сервисный слой, возвращает HTTP-ответы |
| `schemas` | Описывает Pydantic-схемы запросов, ответов и ошибок |
| `posts/service.py` | Содержит бизнес-логику работы с постами и кешированием |
| `posts/repository.py` | Отвечает за чтение и запись данных в PostgreSQL |
| `posts/cache.py` | Отвечает за чтение, запись и удаление данных в Redis |
| `posts/models.py` | Описывает SQLAlchemy-модель таблицы `posts` |
| `core/config.py` | Загружает настройки приложения из `.env` |
| `core/database.py` | Создает подключение к PostgreSQL и управляет сессиями |
| `core/redis.py` | Создает и закрывает Redis-клиент |
| `core/middleware.py` | Добавляет обработку `X-Request-ID` |
| `core/request_context.py` | Хранит request id в контексте текущего запроса |
| `core/logging_config.py` | Настраивает формат логирования |
| `core/exception_handlers.py` | Приводит ошибки API к единому формату |

Разделение на слои делает проект более предсказуемым:

- router не знает, как именно устроены PostgreSQL и Redis;
- service управляет бизнес-сценарием и решает, когда обращаться к кешу;
- repository изолирует SQLAlchemy-запросы;
- cache-слой изолирует работу с Redis;
- схемы отделяют внешние API-контракты от внутренней реализации.

Если в будущем потребуется изменить формат ключей Redis или добавить другой механизм кеширования, основная логика HTTP endpoints останется без изменений.

### Структура проекта

```text
app/
├── api/
│   └── routers/
│       ├── posts.py
│       └── system.py
├── core/
│   ├── config.py
│   ├── database.py
│   ├── errors.py
│   ├── exception_handlers.py
│   ├── logging_config.py
│   ├── middleware.py
│   ├── request_context.py
│   └── redis.py
├── posts/
│   ├── cache.py
│   ├── exceptions.py
│   ├── models.py
│   ├── repository.py
│   └── service.py
├── schemas/
│   ├── errors.py
│   └── posts.py
└── tests/
    ├── unit/
    ├── test_app_lifespan.py
    ├── test_database.py
    ├── test_post_model.py
    ├── test_post_repository.py
    ├── test_post_schemas.py
    ├── test_post_service.py
    ├── test_posts_api.py
    ├── test_posts_cache_api.py
    └── test_request_id_middleware.py
```

### Общая схема приложения

```mermaid
flowchart LR
    Client["Client / Проверяющий"] -->|HTTP REST| API["FastAPI application"]

    API --> SystemRouter["System router"]
    API --> PostsRouter["Posts router"]

    PostsRouter --> PostService["PostService"]

    PostService --> PostRepository["PostRepository"]
    PostService --> PostCache["PostCache"]

    PostRepository -->|SQLAlchemy Async| PostgreSQL[(PostgreSQL)]
    PostCache -->|redis.asyncio| Redis[(Redis)]

    API --> OpenAPI["OpenAPI /docs"]
```

### Поток обработки запроса `GET /posts/{post_id}`

```mermaid
flowchart TD
    A["HTTP request"] --> B["FastAPI router"]
    B --> C["PostService"]
    C --> D["Проверка Redis"]

    D -->|Cache hit| E["Возврат поста из Redis"]
    D -->|Cache miss| F["Чтение поста из PostgreSQL"]

    F --> G["Сохранение поста в Redis с TTL"]

    E --> H["HTTP response"]
    G --> H
```

### Поток обновления поста `PATCH /posts/{post_id}`

```mermaid
flowchart TD
    A["HTTP request"] --> B["FastAPI router"]
    B --> C["PostService"]
    C --> D["Обновление поста в PostgreSQL"]
    D --> E["Удаление старой записи из Redis"]
    E --> F["HTTP response"]
```

### Поток удаления поста `DELETE /posts/{post_id}`

```mermaid
flowchart TD
    A["HTTP request"] --> B["FastAPI router"]
    B --> C["PostService"]
    C --> D["Удаление поста из PostgreSQL"]
    D --> E["Удаление записи из Redis"]
    E --> F["HTTP 204 No Content"]
```

### Роль PostgreSQL и Redis

В проекте PostgreSQL и Redis выполняют разные задачи.

**PostgreSQL** — основной источник актуальных данных. Все операции создания, обновления и удаления выполняются через PostgreSQL.

**Redis** — временный кеш для ускорения повторного чтения постов. Redis не считается главным источником данных: если кеш пустой или запись была удалена, данные можно восстановить из PostgreSQL.

Такой подход позволяет ускорить чтение часто запрашиваемых постов и при этом сохранить PostgreSQL как единственное надежное хранилище актуального состояния.
---

## 5. Переменные окружения

Конфигурация приложения вынесена во внешние переменные окружения.

Это позволяет не хранить настройки подключения, режим запуска и параметры кеширования внутри кода. Один и тот же код может запускаться в разных окружениях: локально, в тестах, на staging или в production, меняя только значения переменных.

В проекте используется два файла:

| Файл | Назначение |
|---|---|
| `.env.example` | Шаблон переменных окружения. Хранится в репозитории и показывает, какие настройки нужны для запуска проекта |
| `.env` | Локальный файл с реальными значениями переменных. Создается вручную и не должен попадать в Git |

Перед первым запуском нужно создать `.env` на основе примера:

```bash
cp .env.example .env
```

После этого приложение и Docker Compose будут использовать значения из `.env`.

### Список переменных

| Переменная | Пример | Назначение |
|---|---|---|
| `APP_NAME` | `blog-cache-api` | Техническое имя сервиса. Используется в healthcheck, логах и служебных ответах |
| `APP_TITLE` | `API для блога с кешированием популярных постов` | Название приложения в OpenAPI/Swagger UI |
| `APP_DESCRIPTION` | `REST API для управления постами с кешированием часто запрашиваемых данных` | Краткое описание сервиса |
| `APP_ENV` | `local` | Текущее окружение приложения: `local`, `test`, `staging`, `production` |
| `APP_VERSION` | `0.1.0` | Версия приложения |
| `API_VERSION` | `v1` | Версия публичного API |
| `DATABASE_URL` | `postgresql+asyncpg://blog_user:blog_password@postgres:5432/blog_cache_db` | Строка подключения к PostgreSQL через asyncpg |
| `REDIS_URL` | `redis://redis:6379/0` | Строка подключения к Redis |
| `SQLALCHEMY_ECHO` | `false` | Включает или отключает вывод SQL-запросов SQLAlchemy в логи |
| `POST_CACHE_TTL_SECONDS` | `300` | Время жизни кешированной записи поста в Redis, в секундах |

### Важные замечания

Для Docker Compose используются внутренние имена сервисов:

```env
DATABASE_URL=postgresql+asyncpg://blog_user:blog_password@postgres:5432/blog_cache_db
REDIS_URL=redis://redis:6379/0
```

Здесь `postgres` и `redis` — это имена сервисов из `docker-compose.yml`, а не адреса на локальной машине.

### Пример `.env`

```env
APP_NAME=blog-cache-api
APP_TITLE="API для блога с кешированием популярных постов"
APP_DESCRIPTION="REST API для управления постами с кешированием часто запрашиваемых данных"
APP_ENV=local
APP_VERSION=0.1.0
API_VERSION=v1

DATABASE_URL=postgresql+asyncpg://blog_user:blog_password@postgres:5432/blog_cache_db
REDIS_URL=redis://redis:6379/0
SQLALCHEMY_ECHO=false
POST_CACHE_TTL_SECONDS=300
```

### Применение изменений

Если изменить значения в `.env`, уже запущенный контейнер может продолжить использовать старые переменные окружения.

Чтобы Docker Compose пересоздал контейнер API с новыми значениями, выполните:

```bash
docker compose up -d --force-recreate api
```

Проверить значение переменной внутри контейнера можно так:

```bash
docker compose exec api printenv APP_TITLE
```
---

## 6. Запуск через Docker Compose

Проект полностью контейнеризирован и запускается через Docker Compose.

Docker Compose поднимает три сервиса:

| Сервис | Назначение |
|---|---|
| `api` | FastAPI-приложение |
| `postgres` | PostgreSQL — основное хранилище данных |
| `redis` | Redis — кеш для часто запрашиваемых постов |

API-сервис подключается к PostgreSQL и Redis через внутреннюю Docker-сеть. Поэтому в `.env` используются имена сервисов `postgres` и `redis`, а не `localhost`.

### Требования

Для локального запуска необходимо:

- установленный Docker;
- установленный Docker Compose;
- свободный порт `8000` на локальной машине для доступа к API;
- свободные внутренние порты PostgreSQL и Redis внутри Docker-сети.

Проверить наличие Docker можно командой:

```bash
docker --version
```

Проверить Docker Compose:

```bash
docker compose version
```

### 1. Подготовить переменные окружения

Перед первым запуском нужно создать локальный `.env` файл на основе шаблона:

```bash
cp .env.example .env
```

Файл `.env.example` хранится в репозитории как пример конфигурации.

Файл `.env` используется локально и не должен попадать в Git.

### 2. Собрать и запустить контейнеры

```bash
docker compose up --build -d
```

Что делает эта команда:

- собирает Docker-образ для FastAPI-приложения;
- создает Docker-сеть проекта;
- создает volumes для PostgreSQL и Redis;
- запускает контейнеры `api`, `postgres` и `redis`;
- оставляет контейнеры работать в фоне благодаря флагу `-d`.

### 3. Проверить состояние контейнеров

```bash
docker compose ps
```

Ожидаемый результат:

- `postgres` находится в состоянии `healthy`;
- `redis` находится в состоянии `healthy`;
- `api` запущен и доступен на порту `8000`.

Примерно это должно выглядеть так:

```text
NAME                         SERVICE    STATUS
blog-cache-api-api-1         api        Up
blog-cache-api-postgres-1    postgres   Up (healthy)
blog-cache-api-redis-1       redis      Up (healthy)
```

Если PostgreSQL или Redis еще не успели стать `healthy`, подождите несколько секунд и повторите команду:

```bash
docker compose ps
```

### 4. Применить миграции базы данных

После запуска контейнеров нужно применить миграции Alembic:

```bash
docker compose exec api alembic upgrade head
```

Эта команда создает актуальную структуру таблиц в PostgreSQL.

Проверить текущую примененную миграцию можно так:

```bash
docker compose exec api alembic current
```

### 5. Проверить, что API отвечает

Проверить базовый healthcheck:

```bash
curl http://localhost:8000/health
```

Пример ответа:

```json
{
  "status": "ok",
  "service": "blog-cache-api",
  "environment": "local"
}
```

Также можно проверить readiness endpoint:

```bash
curl http://localhost:8000/readiness
```

И endpoint с версией сервиса:

```bash
curl http://localhost:8000/version
```

### 6. Открыть Swagger UI

После запуска API доступна интерактивная OpenAPI-документация:

```text
http://localhost:8000/docs
```

Через Swagger UI можно вручную проверить:

- создание поста;
- получение поста по `id`;
- обновление поста;
- удаление поста;
- системные endpoints.

### 7. Проверить CRUD вручную через curl

Создать пост:

```bash
curl -X POST http://localhost:8000/posts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "First post",
    "content": "Post content"
  }'
```

Получить пост:

```bash
curl http://localhost:8000/posts/1
```

Обновить пост:

```bash
curl -X PATCH http://localhost:8000/posts/1 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated title"
  }'
```

Удалить пост:

```bash
curl -i -X DELETE http://localhost:8000/posts/1
```

Для удаления ожидаемый HTTP-статус:

```text
204 No Content
```

### 8. Посмотреть логи приложения

Логи API:

```bash
docker compose logs -f api
```

Логи PostgreSQL:

```bash
docker compose logs -f postgres
```

Логи Redis:

```bash
docker compose logs -f redis
```

Посмотреть последние 100 строк логов API:

```bash
docker compose logs --tail=100 api
```

### 9. Перезапустить API-сервис

Если изменились переменные окружения в `.env`, контейнер API лучше пересоздать:

```bash
docker compose up -d --force-recreate api
```

Если изменился код приложения, можно пересобрать образ:

```bash
docker compose up --build -d api
```

Проверить значение переменной окружения внутри контейнера:

```bash
docker compose exec api printenv APP_TITLE
```

### 10. Остановить контейнеры

Остановить контейнеры без удаления данных PostgreSQL и Redis:

```bash
docker compose down
```

В этом случае Docker volumes сохраняются, и данные останутся между запусками.

### 11. Полностью очистить окружение

Остановить контейнеры и удалить volumes:

```bash
docker compose down -v
```

Эта команда удалит данные PostgreSQL и Redis.

Используйте ее, когда нужно запустить проект полностью с чистого состояния.

### 12. Полный сценарий запуска с нуля

Этот сценарий удобно использовать для финальной проверки проекта:

```bash
docker compose down -v --remove-orphans

cp .env.example .env

docker compose up --build -d

docker compose ps

docker compose exec api alembic upgrade head

curl http://localhost:8000/health
```

После успешного выполнения команд приложение доступно по адресу:

```text
http://localhost:8000
```

Swagger UI:

```text
http://localhost:8000/docs
```
---

## 7. Миграции базы данных

Для управления схемой PostgreSQL в проекте используется **Alembic**.

Миграции позволяют хранить изменения структуры базы данных в коде: создание таблиц, изменение колонок, добавление индексов и другие изменения схемы. Благодаря этому база данных может быть воспроизведена в новом окружении одной командой.

В текущем проекте миграции используются для создания таблицы `posts`.

### Зачем нужны миграции

Миграции решают несколько задач:

- фиксируют историю изменений схемы базы данных;
- позволяют быстро подготовить PostgreSQL после запуска контейнеров;
- делают структуру базы одинаковой у разработчика, проверяющего и в CI;
- позволяют безопасно развивать модели SQLAlchemy;
- дают возможность откатить изменение схемы, если это потребуется.

Без миграций проверяющему пришлось бы вручную создавать таблицы в PostgreSQL. С Alembic достаточно выполнить одну команду после запуска Docker Compose.

### Когда применять миграции

После первого запуска контейнеров необходимо применить миграции:

```bash
docker compose exec api alembic upgrade head
```

Эта команда применяет все миграции до последней доступной версии.

Обычно порядок запуска выглядит так:

```bash
docker compose up --build -d
docker compose exec api alembic upgrade head
```

После этого приложение может работать с актуальной структурой базы данных.

### Проверить текущую миграцию

Чтобы узнать, какая версия миграции сейчас применена в базе данных:

```bash
docker compose exec api alembic current
```

Эта команда полезна, когда нужно убедиться, что база находится в ожидаемом состоянии.

### Посмотреть историю миграций

Чтобы увидеть список всех миграций проекта:

```bash
docker compose exec api alembic history
```

Для более подробного вывода можно использовать:

```bash
docker compose exec api alembic history --verbose
```

### Создать новую миграцию

Если изменилась SQLAlchemy-модель, например добавилась новая колонка в `posts/models.py`, нужно создать новую миграцию:

```bash
docker compose exec api alembic revision --autogenerate -m "describe changes"
```

Пример:

```bash
docker compose exec api alembic revision --autogenerate -m "add post slug"
```

После генерации миграции ее нужно внимательно проверить вручную.

Autogenerate помогает создать файл миграции, но не заменяет ревью. Перед коммитом важно убедиться, что Alembic действительно сгенерировал ожидаемые изменения.

### Применить новую миграцию

После создания миграции применить ее можно так:

```bash
docker compose exec api alembic upgrade head
```

Проверить результат:

```bash
docker compose exec api alembic current
```

### Откатить последнюю миграцию

Откатить базу на одну миграцию назад:

```bash
docker compose exec api alembic downgrade -1
```

Откат полезен при локальной разработке, когда нужно проверить, что миграция корректно применяется и откатывается.

### Полностью пересоздать базу локально

Если нужно проверить проект с чистого состояния, можно удалить Docker volumes и применить миграции заново:

```bash
docker compose down -v
docker compose up --build -d
docker compose exec api alembic upgrade head
```

Команда `docker compose down -v` удаляет данные PostgreSQL и Redis, поэтому использовать ее нужно только для локальной проверки или полного сброса окружения.

### Рекомендуемый порядок работы с миграциями

При изменении моделей порядок действий такой:

```bash
docker compose exec api alembic revision --autogenerate -m "describe changes"
docker compose exec api alembic upgrade head
docker compose exec api python -m pytest
docker compose exec api ruff check app
```

После этого нужно проверить сгенерированный файл миграции и только затем добавлять его в коммит.

### Что важно для проверки задания

Для запуска проекта проверяющему достаточно выполнить:

```bash
docker compose exec api alembic upgrade head
```

Эта команда создает актуальную схему PostgreSQL внутри Docker Compose окружения.
---

## 8. API endpoints

После запуска приложения REST API доступен по адресу:

```text
http://localhost:8000
```

Интерактивная OpenAPI-документация доступна в Swagger UI:

```text
http://localhost:8000/docs
```

Swagger UI позволяет проверить endpoints вручную: создать пост, получить его по `id`, обновить, удалить и посмотреть описание схем запросов и ответов.

API разделен на две группы:

- **системные endpoints** — используются для проверки состояния сервиса;
- **endpoints управления постами** — реализуют CRUD-операции и сценарии кеширования.

### Системные проверки

| Метод | Endpoint | Назначение |
|---|---|---|
| `GET` | `/health` | Проверяет, что приложение запущено и отвечает на HTTP-запросы |
| `GET` | `/readiness` | Проверяет готовность сервиса принимать запросы |
| `GET` | `/version` | Возвращает информацию о версии приложения и API |

#### Проверить healthcheck

```bash
curl http://localhost:8000/health
```

Пример ответа:

```json
{
  "status": "ok",
  "service": "blog-cache-api",
  "environment": "local"
}
```

#### Проверить readiness

```bash
curl http://localhost:8000/readiness
```

Пример ответа:

```json
{
  "status": "ready",
  "checks": {
    "application": "ok"
  }
}
```

#### Проверить версию сервиса

```bash
curl http://localhost:8000/version
```

Пример ответа:

```json
{
  "service": "blog-cache-api",
  "version": "0.1.0",
  "api_version": "v1"
}
```

### Управление постами

| Метод | Endpoint | Назначение |
|---|---|---|
| `POST` | `/posts` | Создать новый пост |
| `GET` | `/posts/{post_id}` | Получить пост по `id` с использованием Redis-кеширования |
| `PATCH` | `/posts/{post_id}` | Частично обновить существующий пост и инвалидировать кеш |
| `DELETE` | `/posts/{post_id}` | Удалить пост и инвалидировать кеш |

### Основные HTTP-статусы

| Статус | Когда используется |
|---|---|
| `200 OK` | Успешное получение или обновление поста |
| `201 Created` | Пост успешно создан |
| `204 No Content` | Пост успешно удален |
| `404 Not Found` | Пост с указанным `id` не найден |
| `422 Unprocessable Entity` | Ошибка валидации входных данных |

### Формат поста

Пример объекта поста в ответе API:

```json
{
  "id": 1,
  "title": "First post",
  "content": "Post content",
  "created_at": "2026-07-06T10:00:00Z",
  "updated_at": "2026-07-06T10:00:00Z"
}
```

### Создать пост

```bash
curl -X POST http://localhost:8000/posts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "First post",
    "content": "Post content"
  }'
```

Ожидаемый результат:

- HTTP-статус `201 Created`;
- в ответе возвращается созданный пост;
- запись сохраняется в PostgreSQL;
- Redis на этом этапе не заполняется, потому что кеш наполняется при чтении.

### Получить пост по id

```bash
curl http://localhost:8000/posts/1
```

Ожидаемый результат:

- HTTP-статус `200 OK`;
- если пост есть в Redis, данные возвращаются из кеша;
- если поста нет в Redis, данные загружаются из PostgreSQL и сохраняются в Redis с TTL.

Именно этот endpoint демонстрирует основной сценарий `cache-aside`.

### Обновить пост

```bash
curl -X PATCH http://localhost:8000/posts/1 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated title"
  }'
```

Ожидаемый результат:

- HTTP-статус `200 OK`;
- пост обновляется в PostgreSQL;
- старая версия поста удаляется из Redis;
- следующий `GET /posts/{post_id}` загрузит актуальные данные из PostgreSQL и заново сохранит их в кеш.

Можно обновить только `title`, только `content` или оба поля сразу.

### Удалить пост

```bash
curl -i -X DELETE http://localhost:8000/posts/1
```

Ожидаемый результат:

```text
HTTP/1.1 204 No Content
```

При удалении:

- пост удаляется из PostgreSQL;
- связанная запись удаляется из Redis;
- повторный запрос `GET /posts/{post_id}` вернет `404 Not Found`.

### Пример ошибки `404 Not Found`

```bash
curl http://localhost:8000/posts/999999
```

Пример ответа:

```json
{
  "error": {
    "code": "post_not_found",
    "message": "Post with id 999999 was not found"
  }
}
```

### Request ID

API поддерживает заголовок `X-Request-ID`.

Его можно передать вручную:

```bash
curl http://localhost:8000/health \
  -H "X-Request-ID: demo-request-1"
```

Приложение вернет этот же request id в HTTP-ответе и добавит его в логи.

Это удобно для отладки: можно связать конкретный HTTP-запрос с записями в логах приложения.

### Проверка сценария кеширования вручную

Создать пост:

```bash
curl -X POST http://localhost:8000/posts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Cache test",
    "content": "This post is used to check Redis cache"
  }'
```

Первый раз получить пост:

```bash
curl http://localhost:8000/posts/1
```

В этом сценарии ожидается `cache miss`: пост загружается из PostgreSQL и сохраняется в Redis.

Повторно получить тот же пост:

```bash
curl http://localhost:8000/posts/1
```

В этом сценарии ожидается `cache hit`: пост может быть возвращен из Redis без дополнительного чтения из PostgreSQL.

Обновить пост:

```bash
curl -X PATCH http://localhost:8000/posts/1 \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Updated content"
  }'
```

После обновления кеш для этого поста удаляется.

Следующий запрос снова загрузит актуальную версию из PostgreSQL:

```bash
curl http://localhost:8000/posts/1
```
---

## 9. Кеширование

В проекте используется паттерн `cache-aside`.

При таком подходе приложение само управляет чтением, наполнением и инвалидацией кеша.

### Основной сценарий

Для запроса `GET /posts/{post_id}` приложение сначала проверяет Redis.

Если пост найден в кеше, приложение возвращает его без обращения к PostgreSQL.

Если запись отсутствует в Redis, приложение загружает пост из PostgreSQL, сохраняет его в Redis с заданным TTL и возвращает клиенту.

PostgreSQL остается основным источником актуальных данных. Redis используется как временный слой для ускорения повторных запросов и снижения нагрузки на базу данных.

### Ключ кеша

Для каждого поста используется ключ:

```text
post:{post_id}
```

Пример:

```text
post:1
```

### TTL кеша

Время жизни кешированной записи управляется через переменную окружения:

```text
POST_CACHE_TTL_SECONDS=300
```

Значение задается в секундах.

В приведенном примере запись о посте будет храниться в Redis не более 300 секунд, после чего Redis автоматически удалит ее.

TTL работает как дополнительная защита от устаревших данных. Основная актуализация кеша выполняется через явную инвалидацию при обновлении или удалении поста.

### Чтение поста

```mermaid
sequenceDiagram
    participant Client as Client
    participant API as FastAPI
    participant Redis as Redis
    participant Postgres as PostgreSQL

    Client->>API: GET /posts/{id}
    API->>Redis: GET post:{id}

    alt Cache hit
        Redis-->>API: Cached post
        API-->>Client: 200 OK
    else Cache miss
        Redis-->>API: null
        API->>Postgres: SELECT post by id
        Postgres-->>API: Post
        API->>Redis: SET post:{id} with TTL
        API-->>Client: 200 OK
    end
```

### Cache hit и cache miss

`Cache hit` происходит, когда Redis уже содержит пост по нужному ключу.

В этом случае приложение возвращает данные из Redis и не выполняет дополнительный запрос в PostgreSQL.

`Cache miss` происходит, когда нужной записи в Redis нет.

В этом случае приложение загружает пост из PostgreSQL, сохраняет его в Redis с TTL и возвращает данные клиенту.

### Инвалидация при обновлении

При обновлении поста приложение:

1. обновляет пост в PostgreSQL;
2. удаляет старую версию поста из Redis.

```mermaid
sequenceDiagram
    participant Client as Client
    participant API as FastAPI
    participant Postgres as PostgreSQL
    participant Redis as Redis

    Client->>API: PATCH /posts/{id}
    API->>Postgres: UPDATE posts
    Postgres-->>API: Updated post
    API->>Redis: DELETE post:{id}
    API-->>Client: 200 OK
```

После следующего `GET /posts/{id}` приложение загрузит свежую версию из PostgreSQL и заново сохранит ее в Redis.

### Инвалидация при удалении

При удалении поста приложение:

1. удаляет пост из PostgreSQL;
2. удаляет пост из Redis.

```mermaid
sequenceDiagram
    participant Client as Client
    participant API as FastAPI
    participant Postgres as PostgreSQL
    participant Redis as Redis

    Client->>API: DELETE /posts/{id}
    API->>Postgres: DELETE FROM posts
    Postgres-->>API: Deleted
    API->>Redis: DELETE post:{id}
    API-->>Client: 204 No Content
```

В штатном сценарии это не позволяет вернуть из кеша старую версию уже удаленного поста.

### Почему выбран cache-aside

`Cache-aside` хорошо подходит для API, где чтение происходит чаще, чем изменение данных.

Преимущества подхода:

- PostgreSQL остается основным источником актуальных данных;
- Redis ускоряет повторное чтение часто запрашиваемых постов;
- кеш можно безопасно удалить и восстановить из PostgreSQL;
- инвалидация при `PATCH` и `DELETE` снижает риск возврата устаревших данных;
- TTL ограничивает максимальное время жизни кешированной записи;
- поведение кеша удобно проверять интеграционными тестами.

### Почему кеш удаляется, а не обновляется вручную

При `PATCH` и `DELETE` кеш удаляется.

Это проще и надежнее, чем вручную синхронно обновлять Redis после каждого изменения.

После удаления кеша следующий `GET /posts/{id}` сам восстановит актуальное значение из PostgreSQL.

Такой подход уменьшает риск рассинхронизации между PostgreSQL и Redis.

---

## 10. Логирование и Request ID

В проекте реализована базовая трассировка HTTP-запросов через заголовок `X-Request-ID`.

`Request ID` — это уникальный идентификатор запроса. Он помогает связать между собой:

- входящий HTTP-запрос;
- выполнение бизнес-логики внутри приложения;
- записи в логах;
- HTTP-ответ, который получил клиент.

Это особенно полезно при отладке API. Если один запрос вызвал ошибку или неожиданное поведение, по его `request_id` можно быстро найти связанные записи в логах.

### Как работает Request ID

Приложение обрабатывает `X-Request-ID` по следующему правилу:

1. Если клиент передал заголовок `X-Request-ID`, приложение использует переданное значение.
2. Если клиент не передал `X-Request-ID`, приложение генерирует новый идентификатор автоматически.
3. Request ID сохраняется в контексте текущего запроса.
4. Request ID добавляется в логи приложения.
5. Request ID возвращается клиенту в HTTP-ответе.

### Пример запроса с X-Request-ID

```bash
curl -i http://localhost:8000/health \
  -H "X-Request-ID: demo-request-1"
```

В ответе приложение вернет этот же заголовок:

```text
X-Request-ID: demo-request-1
```

Это означает, что клиент может передать свой идентификатор запроса и затем использовать его для поиска связанных логов.

### Пример запроса без X-Request-ID

```bash
curl -i http://localhost:8000/health
```

Если заголовок не передан, приложение создаст request id самостоятельно и вернет его в ответе:

```text
X-Request-ID: generated-request-id
```

Фактическое значение будет сгенерировано приложением.

### Просмотр логов API

Посмотреть логи FastAPI-приложения можно командой:

```bash
docker compose logs -f api
```

Посмотреть последние 100 строк:

```bash
docker compose logs --tail=100 api
```

Найти конкретный запрос по request id:

```bash
docker compose logs api | grep "demo-request-1"
```

### Пример проверки трассировки

Создать пост с явным request id:

```bash
curl -X POST http://localhost:8000/posts \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: create-post-demo" \
  -d '{
    "title": "Logging test",
    "content": "This post is used to check request tracing"
  }'
```

После этого можно найти связанные логи:

```bash
docker compose logs api | grep "create-post-demo"
```

Получить пост с другим request id:

```bash
curl http://localhost:8000/posts/1 \
  -H "X-Request-ID: get-post-demo"
```

И найти его в логах:

```bash
docker compose logs api | grep "get-post-demo"
```

### Что логируется

В логах приложения отражаются ключевые операции сервисного слоя:

- создание поста;
- чтение поста;
- cache hit при чтении из Redis;
- cache miss при загрузке из PostgreSQL;
- обновление поста;
- удаление поста;
- инвалидация кеша.

Пример логической связи:

```text
HTTP request
    ↓
X-Request-ID
    ↓
PostService operation
    ↓
log record with request_id
    ↓
HTTP response with X-Request-ID
```

### Зачем это нужно

Request ID делает поведение сервиса наблюдаемым.

Без request id в логах сложно понять, какие записи относятся к одному конкретному HTTP-запросу. Особенно это важно, когда приложение обрабатывает много запросов одновременно.

С request id можно быстро ответить на вопросы:

- какой запрос создал конкретную запись в логах;
- был ли при чтении поста `cache hit` или `cache miss`;
- какой запрос вызвал ошибку;
- вернулось ли клиенту то же значение `X-Request-ID`;
- какие действия выполнил сервис внутри одного HTTP-запроса.

### Важное замечание

В этом проекте логируются технические события и идентификаторы операций, необходимые для отладки и проверки работы приложения.
---

## 11. Тестирование

Запустить все тесты:

```bash
docker compose exec api python -m pytest
```

Запустить тесты API постов:

```bash
docker compose exec api python -m pytest app/tests/test_posts_api.py
```

Запустить интеграционные тесты кеширования:

```bash
docker compose exec api python -m pytest app/tests/test_posts_cache_api.py
```

Запустить unit-тесты сервисного слоя:

```bash
docker compose exec api python -m pytest app/tests/unit/test_post_service_unit.py
```

### Что проверяют тесты кеширования

Интеграционные тесты кеширования проверяют, что:

- `GET /posts/{id}` сохраняет пост в Redis;
- повторный `GET /posts/{id}` может вернуть пост из Redis;
- `PATCH /posts/{id}` удаляет старую запись из Redis;
- после обновления следующий `GET /posts/{id}` возвращает свежие данные;
- `DELETE /posts/{id}` удаляет запись из Redis;
- удаленный пост больше не возвращается из кеша.

---

## 12. Соответствие требованиям задания

| Требование | Статус |
|---|---|
| CRUD для постов | Реализовано |
| PostgreSQL как основная база данных | Реализовано |
| Redis-кеширование при `GET /posts/{id}` | Реализовано |
| Инвалидация кеша при обновлении | Реализовано |
| Инвалидация кеша при удалении | Реализовано |
| Интеграционный тест кеширования | Реализовано |
| Настройки через `.env` | Реализовано |
| README с шагами запуска и тестов | Реализовано |
| Контейнеризация через Docker Compose | Реализовано |
| Архитектурная схема | Реализовано |
| Объяснение выбора cache-aside | Реализовано |

---

## Техническое имя сервиса

```text
blog-cache-api
```
