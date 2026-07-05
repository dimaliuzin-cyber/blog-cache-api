# Blog Cache API

REST API для блога с возможностью кеширования постов

Проект реализован в рамках тестового задания "Вариант Б Проектирование системы с кешированием"

---

## Содержание

- [1. Описание проекта](#1-описание-проекта)
- [2. Возможности](#2-возможности)
- [3. Стек](#3-стек)
- [4. Архитектура](#4-архитектура)
- [5. Переменные окружения](#5-переменные-окружения)
- [6. Запуск через Docker Compose](#6-запуск-через-docker-compose)
- [7. Миграции](#7-миграции)
- [8. API endpoints](#8-api-endpoints)
- [9. Кеширование](#9-кеширование)
- [10. Тесты](#10-тесты)
- [11. Проверка качества кода](#11-проверка-качества-кода)
- [12. Резюме](#12-резюме)

---

## 1. Описание проекта

`Blog Cache API` — это небольшой backend-сервис для управления постами блога.

Сервис предоставляет CRUD API для постов и использует Redis в качестве кеша для операции чтения одного поста по `id`.

Главная идея проекта:

- PostgreSQL хранит основную и актуальную версию данных;
- Redis ускоряет повторное чтение популярных постов;
- FastAPI предоставляет REST API и OpenAPI-документацию;
- Alembic управляет миграциями базы данных;
- Docker Compose поднимает всё окружение.

---

## 2. Возможности

Реализовано:

- создание поста;
- получение поста по `id`;
- частичное обновление поста;
- удаление поста;
- кеширование поста в Redis при чтении;
- чтение поста из Redis при повторном запросе;
- инвалидация кеша при обновлении поста;
- инвалидация кеша при удалении поста;
- TTL для кеша;
- единый формат ошибок;
- Docker Compose окружение с API, PostgreSQL и Redis;
- миграции Alembic;
- логирование ключевых операций;
- request id для трассировки запросов;
- возврат `X-Request-ID` в HTTP-ответах;
- unit-тесты сервисного слоя;
- интеграционные тесты API;
- интеграционные тесты логики кеширования.

---

## 3. Стек

| Компонент | Назначение |
|---|---|
| Python 3.13 | Основной язык разработки |
| FastAPI | HTTP API и OpenAPI-документация |
| Pydantic v2 | Валидация входных и выходных данных |
| pydantic-settings | Загрузка настроек из `.env` |
| PostgreSQL | Основное хранилище данных |
| SQLAlchemy Async ORM | Асинхронная работа с PostgreSQL |
| Alembic | Миграции базы данных |
| Redis | Кеширование постов |
| redis.asyncio | Асинхронный Redis-клиент |
| Docker | Контейнеризация приложения |
| Docker Compose | Запуск API, PostgreSQL и Redis |
| Pytest | Тестирование |
| pytest-asyncio | Асинхронные тесты |
| HTTPX | Интеграционные тесты HTTP API |
| Ruff | Линтинг и форматирование кода |

---

## 4. Архитектура

В проекте использован подход разделения ответственности между слоями приложения: роутеры отвечают за HTTP-интерфейс, сервисы — за бизнес-логику, репозитории — за работу с PostgreSQL, а cache-слой — за взаимодействие с Redis.

| Слой | Ответственность |
|---|---|
| `api/routers` | HTTP endpoints, статусы ответов, зависимости FastAPI |
| `schemas` | Pydantic-схемы запросов, ответов и ошибок |
| `posts/service.py` | Бизнес-логика работы с постами и кешем |
| `posts/repository.py` | Работа с PostgreSQL через SQLAlchemy |
| `posts/cache.py` | Работа с Redis-кешем |
| `posts/models.py` | SQLAlchemy-модель таблицы `posts` |
| `core/config.py` | Настройки приложения из `.env` |
| `core/database.py` | Подключение к PostgreSQL и управление сессиями |
| `core/redis.py` | Создание и закрытие Redis-клиента |
| `core/exception_handlers.py` | Единый формат ошибок |

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
    ├── test_posts_api.py
    ├── test_posts_cache_api.py
    ├── test_post_repository.py
    ├── test_post_service.py
    └── ...
```

### Общая схема

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

### Поток обработки запроса

```text
HTTP request
    ↓
FastAPI router
    ↓
PostService
    ↓
PostRepository / PostCache
    ↓
PostgreSQL / Redis
    ↓
HTTP response
```

---

## 5. Переменные окружения

Настройки приложения хранятся в `.env`.

Пример файла находится в `.env.example`.

Перед запуском приложения необходимо создать файл `.env` в корне проекта на основе `.env.example`:

```bash
cp .env.example .env
```

### Список переменных

| Переменная | Пример | Описание |
|---|---|---|
| `APP_NAME` | `blog-cache-api` | Техническое имя приложения |
| `APP_TITLE` | `Blog Cache API` | Название приложения в OpenAPI |
| `APP_DESCRIPTION` | `API для блога с кешированием популярных постов` | Описание приложения в OpenAPI |
| `APP_ENV` | `local` | Окружение: `local`, `test`, `staging`, `production` |
| `APP_VERSION` | `0.1.0` | Версия приложения |
| `API_VERSION` | `v1` | Версия API |
| `DATABASE_URL` | `postgresql+asyncpg://blog_user:blog_password@postgres:5432/blog_cache_db` | URL подключения к PostgreSQL |
| `REDIS_URL` | `redis://redis:6379/0` | URL подключения к Redis |
| `POST_CACHE_TTL_SECONDS` | `300` | Время жизни кеша поста в Redis в секундах |

---

## 6. Запуск через Docker Compose

### Требования

Для локального запуска требуется:

- Docker;
- Docker Compose;
- свободный порт `8000` на локальной машине для доступа к API;
- PostgreSQL и Redis запускаются отдельными сервисами Docker Compose и доступны API через внутреннюю Docker-сеть.

### 1. Создать `.env`

```bash
cp .env.example .env
```

### 2. Собрать и запустить контейнеры

```bash
docker compose up --build -d
```

Будут запущены сервисы:

| Сервис | Назначение |
|---|---|
| `api` | FastAPI-приложение |
| `postgres` | PostgreSQL база данных |
| `redis` | Redis для кеширования |

### 3. Проверить статус контейнеров

```bash
docker compose ps
```

### 4. Применить миграции

```bash
docker compose exec api alembic upgrade head
```

### 5. Проверить healthcheck

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ:

```json
{
  "status": "ok",
  "service": "blog-cache-api",
  "environment": "local"
}
```

### 6. Открыть Swagger UI

```text
http://localhost:8000/docs
```

### 7. Посмотреть логи API

```bash
docker compose logs -f api
```

### 8. Остановить контейнеры

```bash
docker compose down
```

### 9. Остановить контейнеры и удалить volumes

```bash
docker compose down -v
```

---

## 7. Миграции

Для версионирования и применения изменений схемы базы данных в проекте используется Alembic.

### Применить все миграции

```bash
docker compose exec api alembic upgrade head
```

### Проверить текущую миграцию

```bash
docker compose exec api alembic current
```

### Посмотреть историю миграций

```bash
docker compose exec api alembic history
```

### Создать новую миграцию после изменения моделей

```bash
docker compose exec api alembic revision --autogenerate -m "migration name"
```

### Откатить последнюю миграцию

```bash
docker compose exec api alembic downgrade -1
```

---

## 8. API endpoints

Для проверки и ручного тестирования REST API доступна интерактивная OpenAPI-документация:

```text
http://localhost:8000/docs
```

### System endpoints

| Метод | Endpoint | Описание |
|---|---|---|
| `GET` | `/health` | Проверка, что приложение запущено |
| `GET` | `/readiness` | Базовая проверка готовности приложения |
| `GET` | `/version` | Информация о версии сервиса и API |

### Posts endpoints

| Метод | Endpoint | Описание |
|---|---|---|
| `POST` | `/posts` | Создать пост |
| `GET` | `/posts/{post_id}` | Получить пост по `id` |
| `PATCH` | `/posts/{post_id}` | Частично обновить пост |
| `DELETE` | `/posts/{post_id}` | Удалить пост |

### Пример создания поста

```bash
curl -X POST http://localhost:8000/posts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "First post",
    "content": "Post content"
  }'
```

### Пример получения поста

```bash
curl http://localhost:8000/posts/1
```

### Пример обновления поста

```bash
curl -X PATCH http://localhost:8000/posts/1 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated title"
  }'
```

### Пример удаления поста

```bash
curl -i -X DELETE http://localhost:8000/posts/1
```

---

## 9. Кеширование

В проекте применен паттерн `cache-aside`, при котором приложение явно управляет чтением, наполнением и инвалидацией кеша.

Для запроса `GET /posts/{post_id}` сначала выполняется проверка Redis. Если пост найден в кеше, приложение возвращает его без обращения к PostgreSQL. Если запись отсутствует, данные загружаются из PostgreSQL, после чего сохраняются в Redis с заданным TTL.

PostgreSQL остается основным источником истины для данных приложения. Redis используется как временный слой кеширования, предназначенный для ускорения повторных чтений и снижения нагрузки на базу данных.

При изменении или удалении поста кеш по соответствующему ключу инвалидируется. Такой подход снижает риск возврата устаревших данных после изменения поста: после инвалидации следующий запрос загружает актуальную версию из PostgreSQL и заново наполняет кеш.

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
Значение задается в секундах. В приведенном примере запись о посте будет храниться в Redis не более 300 секунд, после чего Redis автоматически удалит ее.

TTL используется как дополнительный механизм защиты от устаревших данных. Основная актуализация кеша выполняется через явную инвалидацию при обновлении или удалении поста, а TTL ограничивает максимальное время жизни записи на случай непредвиденных сценариев.

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

При чтении поста приложение сначала обращается к Redis.

Если запись найдена в кеше, происходит `cache hit`: приложение возвращает данные из Redis без дополнительного запроса в PostgreSQL. Это ускоряет ответ API и снижает количество повторных чтений из основной базы данных.

Если запись отсутствует в Redis, происходит `cache miss`: приложение загружает пост из PostgreSQL, сериализует результат, сохраняет его в Redis с заданным TTL и возвращает данные клиенту.

Такой сценарий позволяет использовать PostgreSQL как основной источник истины, а Redis — как быстрый временный слой для оптимизации повторных чтений.

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

После следующего `GET /posts/{id}` приложение снова прочитает свежую версию из PostgreSQL и положит ее в Redis.

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

В штатном сценарии это предотвращает возврат из кеша старой версии уже удаленного поста.

### Почему выбран cache-aside

`Cache-aside` выбран потому что он хорошо подходит для REST API с частым чтением и более редкими изменениями данных.

Преимущества подхода:

- простая и понятная логика;
- PostgreSQL остается главным источником данных;
- Redis ускоряет повторные чтения популярных постов;
- кеш можно безопасно удалить и восстановить из PostgreSQL;
- инвалидация при `PATCH` и `DELETE` защищает от возврата устаревших данных;
- TTL дополнительно ограничивает время жизни кеша;
- поведение удобно проверять интеграционными тестами.

### Почему кеш удаляется, а не обновляется вручную

При `PATCH` и `DELETE` кеш именно удаляется.

Это проще и надежнее, чем вручную синхронно обновлять Redis после каждого изменения.

После удаления кеша следующий `GET /posts/{id}` сам восстановит актуальное значение из PostgreSQL.

Такой подход уменьшает риск рассинхронизации между PostgreSQL и Redis.

---

## 10. Тесты

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

### Интеграционные тесты кеширования

Интеграционные тесты проверяют, что:

- `GET /posts/{id}` сохраняет пост в Redis;
- повторный `GET /posts/{id}` может вернуть пост из Redis;
- `PATCH /posts/{id}` удаляет старую запись из Redis;
- после обновления следующий `GET /posts/{id}` возвращает свежие данные;
- `DELETE /posts/{id}` удаляет запись из Redis;
- удаленный пост больше не возвращается из кеша.

---

## 11. Проверка качества кода

Запустить Ruff-проверку:

```bash
docker compose exec api ruff check app
```

Проверить форматирование:

```bash
docker compose exec api ruff format --check app
```

Автоматически отформатировать код:

```bash
docker compose exec api ruff format app
```

---

## 12. Резюме

Проект закрывает ключевые требования тестового задания:

| Требование | Статус |
|---|---|
| CRUD для постов | Реализовано |
| PostgreSQL как основная база данных | Реализовано |
| Redis-кеширование при `GET /posts/{id}` | Реализовано |
| Инвалидация кеша при обновлении | Реализовано |
| Инвалидация кеша при удалении | Реализовано |
| Интеграционный тест кеширования | Реализовано |
| Настройки через `.env` | Реализовано |
| Docker Compose | Реализовано |
| README с запуском и тестами | Реализовано |
| Схема архитектуры | Реализовано |

---

## Короткий сценарий проверки

```bash
cp .env.example .env

docker compose up --build -d

docker compose exec api alembic upgrade head

curl http://localhost:8000/health

docker compose exec api python -m pytest
```

После этого можно открыть Swagger UI:

```text
http://localhost:8000/docs
```
