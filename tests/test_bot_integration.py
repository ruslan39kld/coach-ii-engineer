# -*- coding: utf-8 -*-
"""
Тест интеграции бота с FAQ базой данных
"""
import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import Database
import logging

logging.basicConfig(level=logging.INFO)

print("="*60)
print("ТЕСТ ИНТЕГРАЦИИ БОТА С FAQ")
print("="*60)

# Initialize database
db = Database("data/bot.db")

# Get stats
stats = db.get_stats()
print(f"\n📊 Статистика базы данных:")
print(f"   ❓ FAQ вопросов: {stats.get('faq', 0)}")
print(f"   📚 Документов: {stats['documents']}")
print(f"   📝 Запросов: {stats['queries']}")
print(f"   👥 Пользователей: {stats['users']}")

# Test the main search_documents method (which now searches FAQ first)
print("\n" + "="*60)
print("ТЕСТ МЕТОДА search_documents() - ДОЛЖЕН ИСКАТЬ В FAQ")
print("="*60)

test_query = "как зарегистрироваться в ЕАСУЗ"
print(f"\n🔍 Запрос: '{test_query}'")
results = db.search_documents(test_query, limit=3)
print(f"   Найдено: {len(results)} результатов")

if results:
    for i, result in enumerate(results, 1):
        print(f"\n   {i}. {result['title']}")
        print(f"      Категория: {result.get('category', 'N/A')}")
        print(f"      Источник: {result.get('source_file', 'N/A')}")
        print(f"      Контент (первые 100 символов): {result['content'][:100]}...")
else:
    print("   ⚠️ Ничего не найдено!")

# Test another query
test_query2 = "план-график закупок"
print(f"\n🔍 Запрос: '{test_query2}'")
results2 = db.search_documents(test_query2, limit=3)
print(f"   Найдено: {len(results2)} результатов")

if results2:
    for i, result in enumerate(results2, 1):
        print(f"\n   {i}. {result['title']}")
        print(f"      Категория: {result.get('category', 'N/A')}")

print("\n" + "="*60)
if stats.get('faq', 0) > 0 and len(results) > 0:
    print("✅ ТЕСТ ПРОЙДЕН: FAQ база загружена и работает!")
else:
    print("❌ ТЕСТ НЕ ПРОЙДЕН: Проблемы с FAQ базой")
print("="*60)
