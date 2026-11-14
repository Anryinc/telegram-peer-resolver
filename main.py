import os
import re
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from telethon import TelegramClient, utils
from telethon.sessions import StringSession
from telethon.tl.types import User, Chat, Channel

load_dotenv()

app = FastAPI(
    title="Telegram Peer Resolver",
    description="Резолв Telegram-ссылок и username в peer ID (Bot API формат). Не бот.",
    version="1.0.0",
)

API_ID = int(os.getenv("API_ID") or 0)
API_HASH = os.getenv("API_HASH") or ""
BOT_TOKEN = os.getenv("BOT_TOKEN") or ""
SESSION_STRING = os.getenv("SESSION_STRING") or ""

client: Optional[TelegramClient] = None


@app.on_event("startup")
async def startup_event():
    global client
    if not API_ID or not API_HASH:
        raise RuntimeError("API_ID и API_HASH обязательны")

    if BOT_TOKEN:
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.start(bot_token=BOT_TOKEN)
    elif SESSION_STRING:
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
        await client.start()
    else:
        raise RuntimeError("Укажите BOT_TOKEN или SESSION_STRING")


@app.on_event("shutdown")
async def shutdown_event():
    if client and client.is_connected():
        await client.disconnect()


def extract_username_or_special(link: str) -> tuple[str, Optional[int]]:
    """Возвращает (username_or_clean, special_channel_id_if_tme_c)"""
    link = link.strip()
    if not link:
        raise ValueError("Пустая ссылка")

    # t.me/c/CHANNEL_ID/MSG_ID или похожие
    c_match = re.search(r"t\.me/c/(\d+)", link, re.IGNORECASE)
    if c_match:
        channel_id = int(c_match.group(1))
        return "", channel_id

    # Обычные случаи
    link = link.replace("https://", "").replace("http://", "")
    link = link.replace("t.me/", "").replace("telegram.me/", "")
    if link.startswith("tg://resolve?domain="):
        link = link.split("domain=", 1)[1].split("&")[0]
    link = link.lstrip("@").split("?")[0].split("/")[0]

    if not link or link in ("+", "joinchat"):
        raise ValueError("Не удалось извлечь username из ссылки")

    return link, None


def entity_to_info(entity) -> dict:
    peer_id = utils.get_peer_id(entity)
    info = {"peer_id": peer_id}

    if isinstance(entity, User):
        info["type"] = "bot" if entity.bot else "user"
        info["title"] = " ".join(filter(None, [entity.first_name, entity.last_name])).strip() or None
        info["username"] = entity.username
    elif isinstance(entity, Chat):
        info["type"] = "group"
        info["title"] = entity.title
        info["username"] = None
    elif isinstance(entity, Channel):
        info["type"] = "channel" if entity.broadcast else "supergroup"
        info["title"] = entity.title
        info["username"] = entity.username
    else:
        info["type"] = type(entity).__name__.lower()
        info["title"] = getattr(entity, "title", None)

    return info


@app.get("/")
async def root():
    return {"status": "ok", "message": "Telegram Peer Resolver", "docs": "/docs"}


@app.get("/resolve")
async def resolve(
    link: str = Query(..., description="Ссылка Telegram или @username / username"),
):
    if client is None or not client.is_connected():
        raise HTTPException(status_code=503, detail="Telegram client не инициализирован")

    try:
        username, special_channel_id = extract_username_or_special(link)

        if special_channel_id is not None:
            # Для ссылок вида t.me/c/XXXX/YYYY — ID уже в ссылке
            peer_id = int(f"-100{special_channel_id}")
            return {
                "peer_id": peer_id,
                "type": "channel",
                "title": None,
                "username": None,
                "source": "link_c",
            }

        entity = await client.get_entity(username)
        return entity_to_info(entity)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        msg = str(e)
        if "No user has" in msg or "Cannot find any entity" in msg or "Username not occupied" in msg:
            raise HTTPException(status_code=404, detail="Сущность не найдена")
        raise HTTPException(status_code=400, detail=f"Ошибка резолва: {msg}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
