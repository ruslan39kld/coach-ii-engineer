import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import Database

# Тестовые вопросы
test_queries = [
    "Что такое ЕАСУЗ?",
    "Как создать план-график?",
    "Что такое архивирование объекта?",
    "Как заполнить спецификацию?",
    "Что такое НМЦК?",
    "Как отправить извещение в ЕИС?",
    "Что такое контракт?",
]

db = Database()

print("\n=== ТЕСТ ТОЧНОСТИ ПОИСКА ===\n")

correct = 0
total = len(test_queries)

for i, query in enumerate(test_queries, 1):
    print(f"\n{i}. Вопрос: {query}")
    results = db.search(query, top_k=3)
    
    if results:
        print(f"   ✅ Найдено: {len(results)} результатов")
        print(f"   Лучший: {results[0]['question'][:70]}...")
        correct += 1
    else:
        print("   ❌ Ничего не найдено")

accuracy = (correct / total) * 100
print(f"\n{'='*60}")
print(f"📊 ТОЧНОСТЬ: {accuracy:.1f}% ({correct}/{total})")
print(f"{'='*60}\n")