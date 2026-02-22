import asyncio
import os

import httpx

TOKEN = os.environ.get("BOT_TOKEN", "").strip()
if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in the environment.")

BASE = f"https://api.telegram.org/bot{TOKEN}"


async def diagnose():
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{BASE}/getUpdates", params={"offset": -1, "timeout": 5})
        print("Status:", r.status_code)
        print("Full response:", r.text)


asyncio.run(diagnose())
