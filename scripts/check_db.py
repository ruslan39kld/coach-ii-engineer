import sqlite3
import os

DB_PATH = "data/bot.db"

# Проверяем существование файла
if not os.path.exists(DB_PATH):
    print(f"❌ Файл {DB_PATH} не найден!")
else:
    print(f"✅ Файл {DB_PATH} существует")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Смотрим какие таблицы есть
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("\n📊 Таблицы в базе:")
    if tables:
        for table in tables:
            print(f"   - {table[0]}")
            
            # Считаем записи
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"     Записей: {count}")
    else:
        print("   ❌ НЕТ ТАБЛИЦ!")
    
    conn.close()