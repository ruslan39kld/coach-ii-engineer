# -*- coding: utf-8 -*-
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
print("TESTING FAQ SEARCH")
print("="*60)

# Initialize database
db = Database("data/bot.db")

# Get stats
stats = db.get_stats()
print(f"\n📊 Статистика базы данных:")
print(f"   FAQ вопросов: {stats.get('faq', 0)}")
print(f"   Документов: {stats['documents']}")
print(f"   Запросов: {stats['queries']}")
print(f"   Пользователей: {stats['users']}")

# Test searches
test_queries = [
    "регистрация ЕАСУЗ",
    "план-график",
    "закупка",
    "контракт",
    "заявка"
]

print("\n" + "="*60)
print("ТЕСТИРОВАНИЕ ПОИСКА")
print("="*60)

for query in test_queries:
    print(f"\n🔍 Запрос: '{query}'")
    results = db.search_faq(query, limit=3)
    print(f"   Найдено: {len(results)} результатов")
    
    if results:
        for i, result in enumerate(results[:2], 1):
            print(f"\n   {i}. {result['title']}")
            print(f"      Источник: {result.get('source_file', 'N/A')}")
            print(f"      Контент: {result['content'][:150]}...")

print("\n" + "="*60)
print("ТЕСТ ЗАВЕРШЕН")
print("="*60)
