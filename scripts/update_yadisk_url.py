#!/usr/bin/env python3
"""Обновление ссылки на базу знаний Яндекс.Диск в .env"""

import os

# Новая ссылка на базу знаний
NEW_YADISK_URL = "https://disk.yandex.ru/d/Iq_KsadHSN9-Gg"

# Путь к .env файлу
env_path = os.path.join(os.path.dirname(__file__), '.env')

# Читаем существующий .env
env_lines = []
url_found = False

if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('YADISK_PUBLIC_URL='):
                env_lines.append(f'YADISK_PUBLIC_URL={NEW_YADISK_URL}\n')
                url_found = True
                print(f"[UPDATE] Updated existing YADISK_PUBLIC_URL")
            else:
                env_lines.append(line)
else:
    print("[ERROR] .env file not found!")
    exit(1)

# Если URL не найден, добавляем его
if not url_found:
    env_lines.append(f'\nYADISK_PUBLIC_URL={NEW_YADISK_URL}\n')
    print(f"[ADD] Added new YADISK_PUBLIC_URL")

# Записываем обновленный .env
with open(env_path, 'w', encoding='utf-8') as f:
    f.writelines(env_lines)

print(f"[OK] YADISK_PUBLIC_URL updated successfully!")
print(f"[URL] {NEW_YADISK_URL}")
