import sqlite3
import os

DB_PATH = "data/bot.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    print("🔧 Начинаем миграцию...")
    
    # 1. ПРОВЕРЯЕМ ЕСТЬ ЛИ УЖЕ course_id
    cursor.execute("PRAGMA table_info(lesson_catalog)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'course_id' in columns:
        print("⚠️  Колонка course_id уже существует!")
    else:
        # 2. ДОБАВЛЯЕМ course_id В lesson_catalog
        print("📝 Добавляем course_id в lesson_catalog...")
        cursor.execute("ALTER TABLE lesson_catalog ADD COLUMN course_id INTEGER DEFAULT 1 REFERENCES courses(id)")
        
        # 3. ОБНОВЛЯЕМ ВСЕ СУЩЕСТВУЮЩИЕ УРОКИ (Промт-инженерия)
        print("📝 Устанавливаем course_id=1 для существующих уроков...")
        cursor.execute("UPDATE lesson_catalog SET course_id = 1 WHERE course_id IS NULL")
        
        # 4. СОЗДАЕМ ИНДЕКС
        print("📝 Создаем индекс...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lesson_catalog_course ON lesson_catalog(course_id)")
    
    conn.commit()
    print("\n✅ Миграция выполнена успешно!")
    
    # 5. ПРОВЕРКА
    cursor.execute("""
        SELECT 
            c.name as курс,
            COUNT(l.id) as уроков
        FROM courses c
        LEFT JOIN lesson_catalog l ON c.id = l.course_id
        GROUP BY c.id
    """)
    
    print("\n📊 Результат:")
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]} уроков")
        
except Exception as e:
    print(f"❌ Ошибка: {e}")
    conn.rollback()
finally:
    conn.close()