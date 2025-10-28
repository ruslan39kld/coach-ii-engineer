from database import Database
from claude_service import ClaudeService
import config
import traceback
import sys
import io
import asyncio
import logging

# Исправление кодировки для Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Включить подробное логирование
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

print("\n" + "=" * 80)
print("ПОЛНАЯ ДИАГНОСТИКА БОТА - ЗАПУСК")
print("=" * 80)

results = {"test1": False, "test2": False, "test3": False}

# ============================================================================
# ТЕСТ 1: Проверка базы данных
# ============================================================================
print("\n" + "=" * 80)
print("ТЕСТ 1: ПРОВЕРКА БАЗЫ ДАННЫХ")
print("=" * 80)

try:
    db = Database(config.DB_PATH)
    import sqlite3
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM documents")
    doc_count = cursor.fetchone()[0]
    print(f"\nВсего документов: {doc_count}")
    
    if doc_count == 0:
        print("ОШИБКА: База пустая!")
    else:
        cursor.execute("SELECT id, filename, substr(content, 1, 100), length(content) FROM documents LIMIT 5")
        docs = cursor.fetchall()
        print(f"\nПримеры документов:")
        for doc_id, filename, content, length in docs:
            print(f"\n  [{doc_id}] {filename}")
            print(f"  Начало: {content}...")
            print(f"  Длина: {length} символов")
        results["test1"] = True
        print("\n[OK] ТЕСТ 1 ПРОЙДЕН")
    
    conn.close()
except Exception as e:
    print(f"\n[ERROR] ОШИБКА: {e}")
    traceback.print_exc()

# ============================================================================
# ТЕСТ 2: Проверка поиска
# ============================================================================
print("\n" + "=" * 80)
print("ТЕСТ 2: ПРОВЕРКА ПОИСКА")
print("=" * 80)

try:
    db = Database(config.DB_PATH)
    test_queries = ["заполнить форму", "регистрация заявки", "закупка", "требования", "ГИС ЕАСУЗ"]
    total_found = 0
    
    for query in test_queries:
        print(f"\n[ПОИСК] '{query}'")
        results_search = db.search_documents(query, limit=3)
        if results_search:
            print(f"  [OK] Найдено: {len(results_search)}")
            for i, doc in enumerate(results_search[:2], 1):
                print(f"    {i}. {doc['title'][:50]}...")
            total_found += len(results_search)
        else:
            print(f"  [!] Ничего не найдено")
    
    if total_found > 0:
        results["test2"] = True
        print(f"\n[OK] ТЕСТ 2 ПРОЙДЕН (всего найдено: {total_found})")
    else:
        print(f"\n[FAIL] ТЕСТ 2 ПРОВАЛЕН: поиск не работает")
        
except Exception as e:
    print(f"\n[ERROR] ОШИБКА: {e}")
    traceback.print_exc()

# ============================================================================
# ТЕСТ 3: Проверка Claude
# ============================================================================
print("\n" + "=" * 80)
print("ТЕСТ 3: ПРОВЕРКА CLAUDE С КОНТЕКСТОМ")
print("=" * 80)

async def test_claude():
    try:
        db = Database(config.DB_PATH)
        claude = ClaudeService()
        
        test_question = "как заполнить форму регистрации заявки для участия в закупках"
        print(f"\nВопрос: '{test_question}'")
        
        # Проверяем, какие ключевые слова извлекаются
        keywords = claude._extract_keywords(test_question)
        print(f"\nИзвлеченные ключевые слова: {keywords}")
        
        # Проверяем поиск по ключевым словам
        search_query = " ".join(keywords)
        print(f"Поисковый запрос: '{search_query}'")
        
        docs_by_keywords = db.search_documents(search_query, limit=5)
        print(f"Найдено документов по ключевым словам: {len(docs_by_keywords)}")
        
        if not docs_by_keywords:
            print("[ERROR] Нет документов для Claude - поиск по ключевым словам не работает!")
            print("\nПопробуем более простой запрос...")
            docs_by_keywords = db.search_documents("форма заявка", limit=5)
            print(f"Найдено по 'форма заявка': {len(docs_by_keywords)}")
        
        if docs_by_keywords:
            print("\nДокументы:")
            for i, doc in enumerate(docs_by_keywords, 1):
                print(f"  {i}. {doc['title'][:60]}")
            
            print("\n[Claude] Отправка к Claude...")
            response, response_time = await claude.ask(test_question, db)
            
            print(f"\nОтвет Claude (первые 400 символов):")
            print("─" * 80)
            print(response[:400] + "...")
            print("─" * 80)
            print(f"Время ответа: {response_time}ms")
            
            keywords = ['форм', 'регистр', 'заявк', 'документ', 'заполн']
            found = [kw for kw in keywords if kw in response.lower()]
            
            print(f"\nКлючевые слова в ответе: {len(found)}/{len(keywords)} {found}")
            
            if len(found) >= 2:
                results["test3"] = True
                print("\n[OK] ТЕСТ 3 ПРОЙДЕН")
            else:
                print("\n[WARNING] ТЕСТ 3: Claude не использует контекст правильно")
                
    except Exception as e:
        print(f"\n[ERROR] ОШИБКА: {e}")
        traceback.print_exc()

try:
    asyncio.run(test_claude())
except Exception as e:
    print(f"\n[ERROR] ОШИБКА: {e}")
    traceback.print_exc()

# ============================================================================
# ИТОГИ
# ============================================================================
print("\n" + "=" * 80)
print("ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
print("=" * 80)

print(f"\n{'[OK]' if results['test1'] else '[FAIL]'} Тест 1 (База данных): {'ПРОЙДЕН' if results['test1'] else 'ПРОВАЛЕН'}")
print(f"{'[OK]' if results['test2'] else '[FAIL]'} Тест 2 (Поиск): {'ПРОЙДЕН' if results['test2'] else 'ПРОВАЛЕН'}")
print(f"{'[OK]' if results['test3'] else '[FAIL]'} Тест 3 (Claude): {'ПРОЙДЕН' if results['test3'] else 'ПРОВАЛЕН'}")

passed = sum(results.values())
print(f"\nПройдено тестов: {passed}/3")

if passed == 3:
    print("\n[SUCCESS] ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Бот работает корректно.")
elif passed == 0:
    print("\n[FAIL] ВСЕ ТЕСТЫ ПРОВАЛЕНЫ! Требуется полная диагностика.")
    print("\nВозможные проблемы:")
    print("  1. Документы не загружены в базу")
    print("  2. Функция поиска не работает")
    print("  3. Claude API не настроен или не получает контекст")
else:
    print(f"\n[WARNING] ЧАСТИЧНЫЙ УСПЕХ ({passed}/3). Проверьте проваленные тесты.")

print("\n" + "=" * 80 + "\n")
