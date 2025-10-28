#!/usr/bin/env python3
"""Скрипт для обновления .env файла с новым токеном"""

import os

# Новый токен
NEW_TOKEN = "8260083815:AAF1BfLoMOd8fhfTvlNTXBU9sfwWseG4G8E"

# Путь к .env файлу
env_path = os.path.join(os.path.dirname(__file__), '.env')

# Читаем существующий .env если он есть
env_lines = []
token_found = False

if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('TELEGRAM_BOT_TOKEN='):
                env_lines.append(f'TELEGRAM_BOT_TOKEN={NEW_TOKEN}\n')
                token_found = True
            else:
                env_lines.append(line)
else:
    print("[WARNING] .env file not found, creating new one...")

# Если токен не найден, добавляем его
if not token_found:
    env_lines.append(f'TELEGRAM_BOT_TOKEN={NEW_TOKEN}\n')

# Записываем обновленный .env
with open(env_path, 'w', encoding='utf-8') as f:
    f.writelines(env_lines)

print(f"[OK] Token successfully updated in {env_path}")
print(f"[KEY] New token: {NEW_TOKEN[:20]}...")
