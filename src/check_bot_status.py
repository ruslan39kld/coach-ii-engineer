#!/usr/bin/env python3
"""Check if bot is running and responsive"""

import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot
from telegram.request import HTTPXRequest

load_dotenv()

async def check_status():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0
    )
    
    bot = Bot(token=token, request=request)
    
    try:
        print("[CHECKING] Bot status...")
        me = await bot.get_me()
        print(f"\n[ONLINE] Bot is running!")
        print(f"  Name: {me.first_name}")
        print(f"  Username: @{me.username}")
        print(f"  ID: {me.id}")
        
        # Check for updates
        updates = await bot.get_updates(limit=1)
        print(f"\n[UPDATES] Received {len(updates)} recent updates")
        
        print("\n[SUCCESS] Bot is fully operational!")
        print(f"\n[INFO] You can now message your bot at: https://t.me/{me.username}")
        
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        await bot.shutdown()

if __name__ == "__main__":
    asyncio.run(check_status())
