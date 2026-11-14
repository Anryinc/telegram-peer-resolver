# Telegram Peer Resolver

Сервис для получения **peer ID** по ссылке вида `t.me/username` (и других Telegram-ссылок).

Предназначен для вызова из существующих ботов / бэкендов. **Это не бот**.

Работает только через официальный **Bot API**. Не нужны `API_ID` / `API_HASH` и my.telegram.org.

## Как работает

Принимает:
- `https://t.me/username`
- `t.me/username`
- `@username`
- `username`
- `t.me/c/123456789/42` (для этих ссылок токен даже не нужен)

Возвращает числовой **peer_id** в формате Bot API.

## Эндпоинт

```
GET /resolve?link=https://t.me/username
```

Пример ответа:

```json
{
  "peer_id": -1001234567890,
  "type": "channel",
  "title": "Example Channel",
  "username": "example"
}
```

## Настройка

Нужен только **BOT_TOKEN** любого существующего бота (от @BotFather).

1. Скопируйте `.env.example` → `.env`
2. Вставьте токен:
   ```
   BOT_TOKEN=123456:ABC-DEF...
   ```

## Запуск

```bash
pip install -r requirements.txt
export BOT_TOKEN=твой_токен
uvicorn main:app --reload
```

Или через Docker:

```bash
docker build -t tg-peer-resolver .
docker run -p 8000:8000 -e BOT_TOKEN=твой_токен tg-peer-resolver
```

## Ограничения

- Отлично работает с публичными каналами, группами и ботами.
- Для обычных пользователей Telegram часто возвращает «chat not found», если бот с ними раньше не общался. Это ограничение самого Telegram.
- Ссылки `t.me/c/...` работают без токена.

## Лицензия

MIT
