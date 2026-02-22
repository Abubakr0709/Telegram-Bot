import asyncio
import os

import httpx

TOKEN = os.environ.get("BOT_TOKEN", "").strip()
if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in the environment.")

BASE = f"https://api.telegram.org/bot{TOKEN}"


async def reset():
    async with httpx.AsyncClient(timeout=30) as client:
        print("=== Step 1: Checking webhook info ===")
        r = await client.get(f"{BASE}/getWebhookInfo")
        data = r.json()
        print(data)

        if not data.get("ok"):
            print("\nToken is wrong or invalid. Check BOT_TOKEN and try again.")
            return

        print("\n=== Step 2: Deleting webhook ===")
        r = await client.post(f"{BASE}/deleteWebhook", json={"drop_pending_updates": True})
        print(r.json())

        print("\n=== Step 3: Closing active session ===")
        r = await client.post(f"{BASE}/close")
        print(r.json())

        print("\n=== Waiting 15 seconds... ===")
        await asyncio.sleep(15)

        print("\n=== Step 4: Testing getUpdates ===")
        r = await client.get(f"{BASE}/getUpdates", params={"offset": -1, "timeout": 5})
        print("Status:", r.status_code)
        print("Result:", r.json().get("ok"))


asyncio.run(reset())
