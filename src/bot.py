import asyncio
import logging
import sys
from telegram import Update
from telegram.ext import Application, ContextTypes

import config
from database import Database, KnowledgeBase
from claude_service import ClaudeService
from yadisk_loader import YaDiskLoader

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_PATH, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

async def post_init(application: Application) -> None:
    """Действия при запуске бота"""
    
    print("="*60)
    print("🤖 POST_INIT ВЫЗВАН!")
    print("="*60)
    
    logging.info("="*60)
    logging.info("🤖 ЗАПУСК БОТА ЕАСУЗ 44-ФЗ - POST_INIT")
    logging.info("="*60)
    
    try:
        # Инициализация компонентов
        logging.info("📦 Инициализация Database...")
        database = Database(config.DB_PATH)
        logging.info(f"✅ Database инициализирована: {config.DB_PATH}")
        
        logging.info("🤖 Инициализация ClaudeService...")
        claude_service = ClaudeService()
        logging.info("✅ ClaudeService инициализирован")
        
        logging.info("☁️ Инициализация YaDiskLoader...")
        yadisk_loader = YaDiskLoader(
            public_url=config.YADISK_PUBLIC_URL,
            local_path=config.KB_PATH
        )
        logging.info("✅ YaDiskLoader инициализирован")
        
        logging.info("📚 Инициализация KnowledgeBase...")
        knowledge_base = KnowledgeBase(kb_path=config.KB_PATH, database=database)
        logging.info("✅ KnowledgeBase инициализирована")
    except Exception as e:
        logging.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА при инициализации компонентов: {e}", exc_info=True)
        raise
    
    # Загрузка базы знаний с Яндекс.Диска
    if yadisk_loader.get_file_count() == 0:
        logging.info("📥 Первый запуск - загрузка файлов с Яндекс.Диска...")
        if yadisk_loader.download_all():
            logging.info("✅ Файлы загружены с Яндекс.Диска")
        else:
            logging.warning("⚠️ Не удалось загрузить файлы с Яндекс.Диска")
    else:
        logging.info(f"✅ Найдено локальных файлов: {yadisk_loader.get_file_count()}")
    
    # Индексация документов
    logging.info("📚 Индексация базы знаний...")
    knowledge_base.load_all_files()
    
    # Статистика
    try:
        stats = database.get_stats()
        logging.info(f"✅ FAQ вопросов: {stats.get('faq', 0)}")
        logging.info(f"✅ Документов в базе: {stats['documents']}")
    except Exception as e:
        logging.warning(f"⚠️ Не удалось получить статистику: {e}")
    
    # Сохранение зависимостей в bot_data
    logging.info("💾 Сохранение компонентов в bot_data...")
    application.bot_data['database'] = database
    application.bot_data['claude_service'] = claude_service
    application.bot_data['yadisk_loader'] = yadisk_loader
    application.bot_data['knowledge_base'] = knowledge_base
    logging.info(f"✅ Сохранено в bot_data: {list(application.bot_data.keys())}")
    
    logging.info("="*60)
    logging.info("✅ БОТ ГОТОВ К РАБОТЕ!")
    logging.info("="*60)

async def async_main():
    """Асинхронная главная функция"""
    
    # Проверка обязательных переменных
    if not config.TELEGRAM_BOT_TOKEN:
        logging.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
        raise ValueError("Токен не найден в .env файле")
    
    if not config.CLAUDE_API_KEY:
        logging.error("❌ CLAUDE_API_KEY не установлен!")
        return
    
    # Создание приложения с увеличенным таймаутом и retry логикой
    from telegram.request import HTTPXRequest
    
    # PROXY SUPPORT: Раскомментируйте если нужен прокси для доступа к Telegram
    # proxy_url = "socks5://127.0.0.1:1080"  # Или ваш прокси сервер
    proxy_url = None
    
    # Увеличенные таймауты для стабильного подключения
    request = HTTPXRequest(
        proxy=proxy_url if proxy_url else None,
        connection_pool_size=8,
        connect_timeout=60.0,  # Увеличено с 30 до 60 секунд
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=60.0
    )
    
    application = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .request(request)
        .get_updates_request(request)  # Используем тот же request для get_updates
        .build()
    )
    
    # Регистрация обработчиков
    from handlers import register_handlers
    register_handlers(application)
    
    logging.info("🔧 Инициализация компонентов бота...")
    
    # ВАЖНО: Вручную инициализируем компоненты перед запуском
    try:
        database = Database(config.DB_PATH)
        claude_service = ClaudeService()
        yadisk_loader = YaDiskLoader(
            public_url=config.YADISK_PUBLIC_URL,
            local_path=config.KB_PATH
        )
        knowledge_base = KnowledgeBase(kb_path=config.KB_PATH, database=database)
        
        # Загрузка базы знаний
        if yadisk_loader.get_file_count() == 0:
            logging.info("📥 Загрузка файлов с Яндекс.Диска...")
            yadisk_loader.download_all()
        
        logging.info("📚 Индексация базы знаний...")
        knowledge_base.load_all_files()
        
        stats = database.get_stats()
        logging.info(f"✅ FAQ вопросов: {stats.get('faq', 0)}")
        logging.info(f"✅ Документов в базе: {stats['documents']}")
        
        # Сохранение в bot_data
        application.bot_data['database'] = database
        application.bot_data['claude_service'] = claude_service
        application.bot_data['yadisk_loader'] = yadisk_loader
        application.bot_data['knowledge_base'] = knowledge_base
        
        logging.info(f"✅ Компоненты сохранены в bot_data: {list(application.bot_data.keys())}")
        
    except Exception as e:
        logging.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА при инициализации: {e}", exc_info=True)
        return
    
    # Инициализация и запуск с обработкой ошибок подключения
    logging.info("🚀 Запуск polling...")
    
    max_retries = 3
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            async with application:
                await application.initialize()
                await application.start()
                await application.updater.start_polling(
                    allowed_updates=Update.ALL_TYPES, 
                    drop_pending_updates=True,
                    timeout=60,  # Таймаут для long polling
                    error_callback=lambda error: logging.error(f"⚠️ Polling error: {error}")
                )
                
                logging.info("✅ Бот успешно подключен к Telegram!")
                
                # Ожидание остановки
                try:
                    await asyncio.Event().wait()
                except (KeyboardInterrupt, SystemExit):
                    logging.info("👋 Получен сигнал остановки")
                finally:
                    await application.updater.stop()
                    await application.stop()
                    await application.shutdown()
                break  # Успешное подключение, выходим из цикла retry
                
        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(f"⚠️ Попытка {attempt + 1}/{max_retries} не удалась: {e}")
                logging.info(f"⏳ Повторная попытка через {retry_delay} секунд...")
                await asyncio.sleep(retry_delay)
            else:
                logging.error(f"❌ Не удалось подключиться после {max_retries} попыток")
                logging.error("💡 РЕШЕНИЕ: Проверьте интернет соединение или используйте VPN/прокси")
                raise

def main():
    """Точка входа"""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logging.info("👋 Бот остановлен")
    except Exception as e:
        logging.error(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()