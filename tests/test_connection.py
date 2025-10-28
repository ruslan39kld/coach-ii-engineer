#!/usr/bin/env python3
"""Test script to verify Telegram bot connection"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

token = os.getenv('TELEGRAM_BOT_TOKEN')

if not token:
    print("[ERROR] TELEGRAM_BOT_TOKEN not found in .env file!")
    sys.exit(1)

print(f"[OK] Token loaded: {token[:20]}...")

# Test connection
import asyncio
from telegram import Bot
from telegram.request import HTTPXRequest

async def test_bot():
    print("\n[TEST] Testing connection to Telegram API...")
    
    # Create request with increased timeouts
    request = HTTPXRequest(
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=60.0
    )
    
    bot = Bot(token=token, request=request)
    
    try:
        print("[CONNECTING] Attempting to connect...")
        me = await bot.get_me()
        print(f"\n[SUCCESS] Bot connected successfully!")
        print(f"  Bot ID: {me.id}")
        print(f"  Bot Name: {me.first_name}")
        print(f"  Bot Username: @{me.username}")
        return True
    except Exception as e:
        print(f"\n[FAILED] Connection failed: {e}")
        print("\n[HINT] Possible solutions:")
        print("  1. Check your internet connection")
        print("  2. Verify the token is correct")
        print("  3. Try using a VPN or proxy if Telegram is blocked")
        return False
    finally:
        await bot.shutdown()

if __name__ == "__main__":
    result = asyncio.run(test_bot())
    sys.exit(0 if result else 1)
