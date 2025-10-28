"""Тест формата возвращаемых данных из search_documents"""
import config
from database import Database

print("=" * 60)
print("ТЕСТ ФОРМАТА ДАННЫХ ИЗ search_documents")
print("=" * 60)

db = Database(config.DB_PATH)

# Тестовый поиск
results = db.search_documents("заполнить форму", limit=3)

print(f"\nНайдено документов: {len(results)}")
print(f"Тип результата: {type(results)}")

if results:
    print(f"\nПервый результат:")
    print(f"  Тип: {type(results[0])}")
    print(f"  Ключи: {results[0].keys() if isinstance(results[0], dict) else 'НЕ СЛОВАРЬ!'}")
    
    if isinstance(results[0], dict):
        print(f"\n  id: {results[0].get('id')}")
        print(f"  title: {results[0].get('title', '')[:60]}")
        print(f"  content: {results[0].get('content', '')[:100]}...")
        print(f"  category: {results[0].get('category')}")
        print("\n✅ ФОРМАТ ПРАВИЛЬНЫЙ - СЛОВАРИ")
    else:
        print("\n❌ ОШИБКА: Возвращаются не словари!")
else:
    print("\n⚠️ Документы не найдены")

print("\n" + "=" * 60)
