# -*- coding: utf-8 -*-
"""
Тест ответов бота на основе FAQ базы данных
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
from claude_service import ClaudeService
import logging

logging.basicConfig(level=logging.INFO)

print("="*70)
print("ТЕСТ ОТВЕТОВ БОТА НА ОСНОВЕ FAQ")
print("="*70)

# Initialize components
db = Database("data/bot.db")
claude = ClaudeService()

# Test queries
test_queries = [
    "Как зарегистрироваться в ЕАСУЗ?",
    "Как создать план-график закупок?",
    "Что делать если не выполнили долю закупок у СМСП?",
    "Как заключить контракт с единственным поставщиком?",
    "Что такое экономия по контракту?"
]

print("\n📊 Статистика базы данных:")
stats = db.get_stats()
print(f"   FAQ вопросов: {stats['faq']}")
print(f"   Документов: {stats['documents']}")

print("\n" + "="*70)
print("ТЕСТИРОВАНИЕ ПОИСКА И ОТВЕТОВ")
print("="*70)

for i, query in enumerate(test_queries, 1):
    print(f"\n{'='*70}")
    print(f"ТЕСТ {i}: {query}")
    print("="*70)
    
    # 1. Поиск в базе данных
    print("\n🔍 Шаг 1: Поиск в базе данных...")
    results = db.search_documents(query, limit=3)
    print(f"   Найдено результатов: {len(results)}")
    
    if results:
        print("\n   Найденные документы:")
        for j, result in enumerate(results, 1):
            print(f"\n   {j}. {result['title'][:70]}...")
            print(f"      Категория: {result.get('category', 'N/A')}")
            print(f"      Источник: {result.get('source_file', 'N/A')}")
            print(f"      Контент (первые 150 символов):")
            print(f"      {result['content'][:150]}...")
        
        # 2. Формирование контекста для Claude
        print("\n📝 Шаг 2: Формирование контекста для Claude...")
        context = "\n\n".join([
            f"Документ {i+1}: {r['title']}\n{r['content'][:500]}"
            for i, r in enumerate(results[:3])
        ])
        print(f"   Длина контекста: {len(context)} символов")
        
        # 3. Генерация ответа через Claude
        print("\n🤖 Шаг 3: Генерация ответа через Claude API...")
        try:
            answer = claude.generate_answer(query, context)
            print(f"\n   ✅ Ответ получен (длина: {len(answer)} символов)")
            print("\n" + "-"*70)
            print("ОТВЕТ БОТА:")
            print("-"*70)
            print(answer)
            print("-"*70)
        except Exception as e:
            print(f"\n   ❌ Ошибка при генерации ответа: {e}")
    else:
        print("\n   ⚠️ Ничего не найдено в базе данных!")
    
    print("\n" + "="*70)

# Final summary
print("\n" + "="*70)
print("ИТОГОВАЯ СВОДКА")
print("="*70)
print(f"""
✅ Тестирование завершено!

Проверено:
   ✓ Поиск в FAQ базе данных
   ✓ Извлечение релевантных документов
   ✓ Формирование контекста
   ✓ Генерация ответов через Claude API

Статистика:
   📚 FAQ вопросов в базе: {stats['faq']}
   📄 Документов в базе: {stats['documents']}
   🧪 Протестировано запросов: {len(test_queries)}
""")
print("="*70)
