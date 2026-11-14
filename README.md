# Telegram Peer Resolver

Сервис для получения **peer ID** по ссылке или username в Telegram.

Предназначен для вызова из существующих ботов / бэкендов. **Это не бот**.

## Как работает

Принимает ссылку (`https://t.me/username`, `t.me/username`, `@username`, `tg://resolve?domain=...`, ссылки вида `t.me/c/...`) и возвращает числовой **peer_id** в формате Bot API:

- Пользователи / боты → положительное число
- Обычные группы → отрицательное число
- Каналы / супергруппы → число вида `-100xxxxxxxxxx`

## Эндпоинты

### `GET /resolve?link=...`

Параметр `link` — любая Telegram-ссылка или username.

Пример ответа:

```json
{
  "peer_id": -1001234567890,
  "type": "channel",
  "title": "Example Channel",
  "username": "example"
}
```

### `GET /`

Статус сервиса.

### `GET /docs`

Swagger UI.

## Настройка

1. Получите `API_ID` и `API_HASH` на [my.telegram.org](https://my.telegram.org).
2. Создайте бота у @BotFather и возьмите `BOT_TOKEN` (рекомендуется для простоты).

   Или используйте строку сессии пользовательского аккаунта (`SESSION_STRING`) — это надёжнее для произвольных пользователей.

3. Скопируйте `.env.example` в `.env` и заполните значения.

## Запуск локально

```bash
pip install -r requirements.txt
export API_ID=...
export API_HASH=...
export BOT_TOKEN=...
# или SESSION_STRING=...
uvicorn main:app --reload
```

## Деплой

Подходит для Railway, Render, Fly.io, Docker и т.д.

Пример для Docker:

```bash
docker build -t tg-peer-resolver .
docker run -p 8000:8000 -e API_ID=... -e API_HASH=... -e BOT_TOKEN=... tg-peer-resolver
```

## Ограничения

- Для приватных чатов / пользователей без публичного username резолв может не сработать.
- Telegram может ограничивать частые запросы (FloodWait). Добавьте кэш при необходимости.
- Сервис использует MTProto (Telethon). Бот-токен подходит для большинства публичных сущностей.

## Лицензия

MIT
