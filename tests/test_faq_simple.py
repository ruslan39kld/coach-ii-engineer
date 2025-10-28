# -*- coding: utf-8 -*-
"""
Простое тестирование FAQ базы (БЕЗ Claude AI)
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
print("🔍 ТЕСТИРОВАНИЕ FAQ БАЗЫ")
print("="*60)

# Инициализация
database = Database("data/bot.db")
stats = database.get_stats()

print(f"\n📊 Статистика:")
print(f"   ❓ FAQ вопросов: {stats.get('faq', 0)}")
print(f"   📚 Документов: {stats['documents']}")

if stats.get('faq', 0) == 0:
    print("\n⚠️ FAQ база пуста! Запустите: python load_faq_win.py")
    sys.exit(1)

print("\n" + "="*60)
print("ИНТЕРАКТИВНЫЙ ПОИСК В FAQ")
print("="*60)
print("\nВведите поисковый запрос (или 'exit' для выхода)")
print("\nПримеры:")
print("  - регистрация")
print("  - план-график")
print("  - контракт")
print("  - закупка")
print("="*60)

while True:
    try:
        print("\n" + "-"*60)
        query = input("🔍 Поиск: ").strip()
        
        if not query:
            continue
            
        if query.lower() in ['exit', 'quit', 'выход']:
            print("\n👋 До свидания!")
            break
        
        # Поиск в FAQ
        results = database.search_faq(query, limit=5)
        
        if not results:
            print(f"\n❌ По запросу '{query}' ничего не найдено")
            print("💡 Попробуйте другие ключевые слова")
            continue
        
        print(f"\n✅ Найдено: {len(results)} результатов")
        print("="*60)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"   📄 Источник: {result.get('source_file', 'N/A')}")
            
            # Показываем полный ответ
            content = result['content']
            if 'Ответ:' in content:
                parts = content.split('Ответ:', 1)
                answer = parts[1].strip()
                print(f"\n   💬 Ответ:")
                # Выводим первые 300 символов ответа
                if len(answer) > 300:
                    print(f"   {answer[:300]}...")
                    print(f"   (показано {len(answer)} символов)")
                else:
                    print(f"   {answer}")
            
            print("-"*60)
        
    except KeyboardInterrupt:
        print("\n\n👋 Поиск завершен!")
        break
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
