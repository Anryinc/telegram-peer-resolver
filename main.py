import os
import re
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query

load_dotenv()

app = FastAPI(
    title="Telegram Peer Resolver",
    description="Резолв Telegram-ссылок (t.me/username и др.) в peer ID через Bot API. Не бот.",
    version="2.0.0",
)

BOT_TOKEN = os.getenv("BOT_TOKEN") or ""
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else ""


def extract_username_or_special(link: str) -> tuple[str, Optional[int]]:
    """Возвращает (username, special_channel_id_if_tme_c)"""
    link = link.strip()
    if not link:
        raise ValueError("Пустая ссылка")

    # t.me/c/CHANNEL_ID/... — ID уже в ссылке
    c_match = re.search(r"t\.me/c/(\d+)", link, re.IGNORECASE)
    if c_match:
        return "", int(c_match.group(1))

    # Очистка до username
    link = link.replace("https://", "").replace("http://", "")
    link = link.replace("t.me/", "").replace("telegram.me/", "")
    if "domain=" in link:
        link = link.split("domain=", 1)[1].split("&")[0]
    link = link.lstrip("@").split("?")[0].split("/")[0]

    if not link or link in ("+", "joinchat"):
        raise ValueError("Не удалось извлечь username из ссылки")

    return link, None


async def resolve_via_bot_api(username: str) -> dict:
    if not BOT_TOKEN:
        raise HTTPException(status_code=500, detail="BOT_TOKEN не задан")

    async with httpx.AsyncClient(timeout=15.0) as client:
        # getChat принимает @username или username
        resp = await client.get(f"{API_BASE}/getChat", params={"chat_id": f"@{username}"})
        data = resp.json()

    if not data.get("ok"):
        description = data.get("description", "unknown error")
        if "chat not found" in description.lower() or "not found" in description.lower():
            raise HTTPException(status_code=404, detail="Сущность не найдена или недоступна")
        raise HTTPException(status_code=400, detail=f"Telegram API: {description}")

    result = data["result"]
    peer_id = result["id"]
    chat_type = result.get("type", "unknown")

    # Приводим тип к понятному виду
    type_map = {
        "private": "user",
        "group": "group",
        "supergroup": "supergroup",
        "channel": "channel",
    }
    friendly_type = type_map.get(chat_type, chat_type)

    title = result.get("title") or result.get("first_name")
    if result.get("last_name"):
        title = f"{title or ''} {result['last_name']}".strip()

    return {
        "peer_id": peer_id,
        "type": friendly_type,
        "title": title,
        "username": result.get("username"),
    }


@app.get("/")
async def root():
    return {"status": "ok", "message": "Telegram Peer Resolver (Bot API)", "docs": "/docs"}


@app.get("/resolve")
async def resolve(
    link: str = Query(..., description="Ссылка вида t.me/username, https://t.me/username, @username или t.me/c/..."),
):
    try:
        username, special_channel_id = extract_username_or_special(link)

        # Специальный случай — ID уже в ссылке, токен не нужен
        if special_channel_id is not None:
            peer_id = int(f"-100{special_channel_id}")
            return {
                "peer_id": peer_id,
                "type": "channel",
                "title": None,
                "username": None,
                "source": "link_c",
            }

        return await resolve_via_bot_api(username)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
