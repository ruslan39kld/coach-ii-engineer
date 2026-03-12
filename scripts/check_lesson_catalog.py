import sqlite3

DB_PATH = "data/bot.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Смотрим структуру таблицы
cursor.execute("PRAGMA table_info(lesson_catalog)")
columns = cursor.fetchall()

print("📊 Структура таблицы lesson_catalog:")
print("-" * 50)
for col in columns:
    print(f"  {col[1]:<20} {col[2]:<10} {'NOT NULL' if col[3] else ''}")

conn.close()