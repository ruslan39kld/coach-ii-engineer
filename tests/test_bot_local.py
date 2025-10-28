# -*- coding: utf-8 -*-
"""
Локальное тестирование бота БЕЗ Telegram
Проверяет работу FAQ базы и Claude AI
"""
import sys
import os
import asyncio

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import Database
from claude_service import ClaudeService
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("="*60)
print("🤖 ЛОКАЛЬНОЕ ТЕСТИРОВАНИЕ БОТА")
print("="*60)

# Инициализация компонентов
print("\n📦 Инициализация компонентов...")
database = Database("data/bot.db")
claude_service = ClaudeService()

# Статистика
stats = database.get_stats()
print(f"\n📊 Статистика базы данных:")
print(f"   ❓ FAQ вопросов: {stats.get('faq', 0)}")
print(f"   📚 Документов: {stats['documents']}")
print(f"   📝 Запросов: {stats['queries']}")
print(f"   👥 Пользователей: {stats['users']}")

if stats.get('faq', 0) == 0:
    print("\n⚠️ ВНИМАНИЕ: FAQ база пуста!")
    print("   Запустите: python load_faq_win.py")
    sys.exit(1)

print("\n" + "="*60)
print("✅ БОТ ГОТОВ К ТЕСТИРОВАНИЮ")
print("="*60)
print("\nВведите вопрос (или 'exit' для выхода):")
print("Примеры вопросов:")
print("  - Как зарегистрироваться в ЕАСУЗ?")
print("  - Как создать план-график?")
print("  - Что такое контракт?")
print("="*60)

async def test_query(question: str):
    """Тестирование запроса"""
    print(f"\n🔍 Ваш вопрос: {question}")
    print("⏳ Обработка...")
    
    try:
        # Получаем ответ от Claude
        answer, response_time = await claude_service.ask(question, database)
        
        print("\n" + "="*60)
        print("💬 ОТВЕТ БОТА:")
        print("="*60)
        print(answer)
        print("="*60)
        print(f"⏱️ Время ответа: {response_time}ms")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        logging.error(f"Error: {e}", exc_info=True)

# Интерактивный режим
while True:
    try:
        print("\n" + "-"*60)
        user_input = input("❓ Ваш вопрос: ").strip()
        
        if not user_input:
            continue
            
        if user_input.lower() in ['exit', 'quit', 'выход']:
            print("\n👋 До свидания!")
            break
        
        # Запускаем асинхронный запрос
        asyncio.run(test_query(user_input))
        
    except KeyboardInterrupt:
        print("\n\n👋 Тестирование завершено!")
        break
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        logging.error(f"Error in main loop: {e}", exc_info=True)
