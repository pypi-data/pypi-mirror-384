import os
import asyncio
from dotenv import load_dotenv
from tests.vpn_bot import Client
from tests.vpn_bot.api.payments.get_payment_methods import sync, asyncio as async_get

load_dotenv()
client = Client(
    base_url=os.getenv("VPN_BOT_BASE_URL"),
    headers={"x-telegram-authorization": os.getenv("TELEGRAM_AUTH_DATA")}
)

async def test():
    print("Testing sync request...")
    sync_result = sync(client=client)
    print(f"Sync result: {sync_result}")
    
    print("Testing async request...")
    async_result = await async_get(client=client)
    print(f"Async result: {async_result}")

if __name__ == "__main__":
    asyncio.run(test())