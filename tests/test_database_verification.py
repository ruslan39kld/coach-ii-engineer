# -*- coding: utf-8 -*-
"""
Полная проверка базы данных и FAQ
"""
import sys
import os
import sqlite3

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import Database
import logging

logging.basicConfig(level=logging.INFO)

print("="*70)
print("ПОЛНАЯ ПРОВЕРКА БАЗЫ ДАННЫХ И FAQ")
print("="*70)

# Initialize database
db_path = "data/bot.db"
db = Database(db_path)

# 1. Проверка структуры базы данных
print("\n📋 1. ПРОВЕРКА СТРУКТУРЫ БАЗЫ ДАННЫХ")
print("-"*70)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Получить список всех таблиц
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print(f"Найдено таблиц: {len(tables)}")
for table in tables:
    table_name = table[0]
    print(f"\n📊 Таблица: {table_name}")
    
    # Получить структуру таблицы
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    for col in columns:
        print(f"   - {col[1]} ({col[2]})")
    
    # Получить количество записей
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"   Записей: {count}")

# 2. Детальная проверка FAQ таблицы
print("\n" + "="*70)
print("📚 2. ДЕТАЛЬНАЯ ПРОВЕРКА FAQ ТАБЛИЦЫ")
print("-"*70)

cursor.execute("SELECT COUNT(*) FROM faq")
faq_count = cursor.fetchone()[0]
print(f"\nВсего FAQ записей: {faq_count}")

# Получить примеры FAQ
cursor.execute("SELECT id, question, answer, source_file FROM faq LIMIT 5")
faq_samples = cursor.fetchall()

print("\nПримеры FAQ записей:")
for i, faq in enumerate(faq_samples, 1):
    print(f"\n{i}. ID: {faq[0]}")
    print(f"   Вопрос: {faq[1][:80]}...")
    print(f"   Ответ: {faq[2][:80]}...")
    print(f"   Источник: {faq[3]}")

# Проверить источники FAQ
cursor.execute("SELECT DISTINCT source_file FROM faq")
sources = cursor.fetchall()
print(f"\nИсточники FAQ ({len(sources)}):")
for source in sources[:10]:  # Показать первые 10
    cursor.execute("SELECT COUNT(*) FROM faq WHERE source_file = ?", (source[0],))
    count = cursor.fetchone()[0]
    print(f"   - {source[0]}: {count} записей")

# 3. Проверка таблицы documents
print("\n" + "="*70)
print("📄 3. ПРОВЕРКА ТАБЛИЦЫ DOCUMENTS")
print("-"*70)

cursor.execute("SELECT COUNT(*) FROM documents")
docs_count = cursor.fetchone()[0]
print(f"\nВсего документов: {docs_count}")

# Получить категории документов
cursor.execute("SELECT DISTINCT category FROM documents")
categories = cursor.fetchall()
print(f"\nКатегории документов ({len(categories)}):")
for cat in categories:
    cursor.execute("SELECT COUNT(*) FROM documents WHERE category = ?", (cat[0],))
    count = cursor.fetchone()[0]
    print(f"   - {cat[0]}: {count} документов")

# Примеры документов
cursor.execute("SELECT id, filename, category FROM documents LIMIT 5")
doc_samples = cursor.fetchall()
print("\nПримеры документов:")
for i, doc in enumerate(doc_samples, 1):
    print(f"{i}. {doc[1]} (Категория: {doc[2]})")

# 4. Проверка таблицы queries
print("\n" + "="*70)
print("📝 4. ПРОВЕРКА ТАБЛИЦЫ QUERIES (ИСТОРИЯ ЗАПРОСОВ)")
print("-"*70)

cursor.execute("SELECT COUNT(*) FROM queries")
queries_count = cursor.fetchone()[0]
print(f"\nВсего запросов: {queries_count}")

if queries_count > 0:
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM queries")
    users_count = cursor.fetchone()[0]
    print(f"Уникальных пользователей: {users_count}")
    
    # Последние запросы
    cursor.execute("SELECT username, query, created_at FROM queries ORDER BY created_at DESC LIMIT 5")
    recent_queries = cursor.fetchall()
    print("\nПоследние запросы:")
    for i, q in enumerate(recent_queries, 1):
        print(f"{i}. {q[0]}: {q[1][:50]}... ({q[2]})")

conn.close()

# 5. Тестирование поиска в FAQ
print("\n" + "="*70)
print("🔍 5. ТЕСТИРОВАНИЕ ПОИСКА В FAQ")
print("-"*70)

test_queries = [
    "регистрация в ЕАСУЗ",
    "план-график закупок",
    "контракт с единственным поставщиком",
    "СМСП закупки",
    "экономия по контракту"
]

for query in test_queries:
    print(f"\n🔎 Запрос: '{query}'")
    results = db.search_faq(query, limit=3)
    print(f"   Найдено: {len(results)} результатов")
    
    if results:
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result['title'][:60]}...")
    else:
        print("   ⚠️ Ничего не найдено")

# 6. Итоговая статистика
print("\n" + "="*70)
print("📊 6. ИТОГОВАЯ СТАТИСТИКА")
print("-"*70)

stats = db.get_stats()
print(f"""
✅ База данных успешно проверена!

Статистика:
   📚 FAQ вопросов: {stats['faq']}
   📄 Документов: {stats['documents']}
   📝 Запросов пользователей: {stats['queries']}
   👥 Уникальных пользователей: {stats['users']}
""")

# Финальная проверка
print("="*70)
if stats['faq'] > 0:
    print("✅ ПРОВЕРКА ПРОЙДЕНА: База данных и FAQ работают корректно!")
else:
    print("❌ ПРОВЕРКА НЕ ПРОЙДЕНА: FAQ база пуста!")
print("="*70)
