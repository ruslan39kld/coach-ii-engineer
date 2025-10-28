#!/usr/bin/env python3
"""Send a test message to verify bot is responding"""

import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot
from telegram.request import HTTPXRequest

load_dotenv()

async def send_test():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    admin_ids = os.getenv('ADMIN_IDS', '').split(',')
    
    if not admin_ids or not admin_ids[0].strip():
        print("[INFO] No ADMIN_IDS configured in .env")
        print("[INFO] Please add your Telegram user ID to .env file:")
        print("       ADMIN_IDS=your_telegram_user_id")
        print("\n[INFO] To get your user ID:")
        print("       1. Message the bot @easuz44fz_bot")
        print("       2. Check the logs for your user ID")
        return
    
    chat_id = admin_ids[0].strip()
    
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0
    )
    
    bot = Bot(token=token, request=request)
    
    try:
        print(f"[SENDING] Test message to chat_id: {chat_id}")
        await bot.send_message(
            chat_id=chat_id,
            text="🤖 Тестовое сообщение!\n\nБот ЕАСУЗ 44-ФЗ успешно запущен и работает!"
        )
        print("[SUCCESS] Test message sent!")
        
    except Exception as e:
        print(f"[ERROR] Failed to send message: {e}")
        print("\n[HINT] Make sure:")
        print("  1. You have started a conversation with @easuz44fz_bot")
        print("  2. Your user ID is correct in .env ADMIN_IDS")
        
    finally:
        await bot.shutdown()

if __name__ == "__main__":
    asyncio.run(send_test())
