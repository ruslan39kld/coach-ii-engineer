# -*- coding: utf-8 -*-
"""
Простой тест для проверки базы данных и FAQ
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

print("="*60)
print("ПРОСТОЙ ТЕСТ БАЗЫ ДАННЫХ И FAQ")
print("="*60)

# Инициализация базы данных
db = Database("data/bot.db")

# Получить статистику
stats = db.get_stats()

print(f"""
📊 СТАТИСТИКА БАЗЫ ДАННЫХ:

   📚 FAQ вопросов:        {stats['faq']}
   📄 Документов:          {stats['documents']}
   📝 Запросов:            {stats['queries']}
   👥 Пользователей:       {stats['users']}
""")

# Тестовые запросы
print("="*60)
print("ТЕСТ ПОИСКА В FAQ")
print("="*60)

queries = [
    "регистрация в ЕАСУЗ",
    "план-график",
    "экономия по контракту"
]

for query in queries:
    print(f"\n🔍 Запрос: '{query}'")
    results = db.search_faq(query, limit=2)
    
    if results:
        print(f"   ✅ Найдено: {len(results)} результатов")
        for i, r in enumerate(results, 1):
            print(f"   {i}. {r['title'][:60]}...")
    else:
        print("   ❌ Ничего не найдено")

print("\n" + "="*60)
if stats['faq'] > 0:
    print("✅ ТЕСТ ПРОЙДЕН: База данных работает!")
else:
    print("❌ ОШИБКА: FAQ база пуста!")
print("="*60)
