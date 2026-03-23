"""
Главный файл бота ИИ Инженер
С интеграцией системы отслеживания прогресса и админ-панели
Версия: ИСПРАВЛЕННАЯ - правильная активность
"""

import asyncio
import logging
import os
import re
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BotCommand
from aiogram.fsm.context import FSMContext

import config
from services.database import Database
from services.claude_service import ClaudeService

# Добавляем путь к database (она на уровень выше src)
sys.path.insert(0, str(Path(__file__).parent.parent))

# Импорт системы прогресса
from database.db_manager import db as progress_db
from handlers.admin_handler import (
    admin_command,
    handle_admin_callback,
    is_admin
)
from handlers.progress_handler import (
    show_user_activity,
    start_course_tracking,
    complete_lesson_tracking
)

# Импорт существующих handlers
from handlers import menu, learning, testing, trainer, navigator, consultant
from handlers.learning import user_modes
from handlers.testing import user_test_state

# ============================================================================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ============================================================================

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_PATH, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# ============================================================================
# ГЛОБАЛЬНЫЕ КОМПОНЕНТЫ
# ============================================================================

_components = {}


def _load_lessons_from_files(database):
    """
    Автоматически загружает уроки из файлов на диске в lesson_catalog.

    Сканирует config.LESSONS_DIR рекурсивно в поисках файлов urok*.txt.
    Номер урока извлекается из имени файла (urokN_*.txt → N).
    Номер модуля извлекается из имени папки (МОДУЛЬ N / Модуль N → N).
    course_id определяется по имени папки: 'vibe' → 2, 'web'/'веб' → 3, иначе → 1.
    """
    lessons_dir = config.LESSONS_DIR

    if not os.path.isdir(lessons_dir):
        logger.warning(
            f"⚠️ Папка с уроками не найдена: {lessons_dir}. "
            "Поместите файлы уроков в эту папку для автозагрузки."
        )
        return

    loaded = 0
    for dirpath, _, filenames in os.walk(lessons_dir):
        for filename in sorted(filenames):
            if not re.match(r'urok\d+.*\.txt$', filename, re.IGNORECASE):
                continue

            m_lesson = re.match(r'urok(\d+)', filename, re.IGNORECASE)
            if not m_lesson:
                continue
            lesson_no = int(m_lesson.group(1))

            # Извлекаем module_no из пути папки
            module_no = 1
            for part in Path(dirpath).parts:
                m_mod = re.search(r'(?:МОДУЛЬ|Модуль|module)\s*(\d+)', part, re.IGNORECASE)
                if m_mod:
                    module_no = int(m_mod.group(1))
                    break

            # Определяем course_id по имени папки
            course_id = 1
            full_path_lower = dirpath.lower()
            if 'vibe' in full_path_lower:
                course_id = 2
            elif 'web' in full_path_lower or 'веб' in full_path_lower:
                course_id = 3

            filepath = os.path.join(dirpath, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Пробуем извлечь заголовок из содержимого
                title_match = re.search(r'УРОК\s+\d+[:.]\s*(.+)', content)
                if title_match:
                    title = title_match.group(1).strip()
                else:
                    title = filename.replace('.txt', '').replace('_', ' ').strip()

                database.add_lesson_to_catalog(module_no, lesson_no, title, filepath, content, course_id)
                loaded += 1
                logger.info(f"  ✅ курс={course_id} M{module_no} L{lesson_no}: {title[:60]}")
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки файла {filepath}: {e}")

    if loaded > 0:
        logger.info(f"✅ Автозагрузка уроков завершена: {loaded} уроков из {lessons_dir}")
    else:
        logger.warning(f"⚠️ Файлы уроков (urok*.txt) не найдены в {lessons_dir}")


async def init_components():
    """Инициализация всех компонентов бота"""
    global _components
    try:
        logger.info("🔄 Инициализация компонентов...")
        
        # Существующие компоненты
        database = Database(config.DB_PATH)

        # Автозагрузка уроков, если каталог пуст
        if not database.get_all_lessons():
            logger.info("📚 Каталог уроков пуст — запускаем автозагрузку из файлов...")
            _load_lessons_from_files(database)

        claude_service = ClaudeService()
        
        _components.update({
            'database': database,
            'claude_service': claude_service,
            'progress_db': progress_db  # Добавляем БД прогресса
        })
        
        logger.info("✅ Все компоненты загружены успешно")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации: {e}", exc_info=True)
        return False

# ============================================================================
# MIDDLEWARE ДЛЯ РЕГИСТРАЦИИ ПОЛЬЗОВАТЕЛЕЙ
# ============================================================================

async def register_user_middleware(handler, event, data):
    """Автоматическая регистрация пользователей в БД прогресса"""
    if hasattr(event, 'from_user') and event.from_user:
        user = event.from_user
        try:
            progress_db.register_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
        except Exception as e:
            logger.warning(f"Ошибка регистрации пользователя {user.id}: {e}")
    
    return await handler(event, data)

# ============================================================================
# ОБРАБОТЧИКИ ТЕКСТОВЫХ СООБЩЕНИЙ
# ============================================================================

async def handle_text_message(message: types.Message):
    """Обработка текстовых сообщений"""
    user_id = message.from_user.id
    mode = user_modes.get(user_id, "consultant")
    
    db = _components['database']
    claude = _components['claude_service']
    
    # Логируем активность
    try:
        progress_db.update_user_activity(user_id)
    except:
        pass
    
    # Режим тестирования
    if mode == "testing":
        await testing.handle_test_answer(message, db)
        return
    
    # Режим тренажера
    if mode == "trainer":
        await trainer.analyze_prompt(message, claude, user_id)
        return
    
    # Режим консультанта
    if mode == "consultant":
        await consultant.handle_consultant_question(message, db, claude, user_id)
        return
    
    await message.answer("⚠️ Выберите режим через /start")

# ============================================================================
# WRAPPER ФУНКЦИИ ДЛЯ ОБУЧЕНИЯ (С ОТСЛЕЖИВАНИЕМ ПРОГРЕССА)
# ============================================================================

async def wrapped_start_learning(callback: types.CallbackQuery, state: FSMContext):
    """Начало обучения с записью на курс"""
    db = _components['database']
    user_id = callback.from_user.id
    
    # Записываем на курс (по умолчанию prompt_engineering)
    try:
        await start_course_tracking(callback, 'prompt_engineering')
    except Exception as e:
        logger.error(f"Ошибка записи на курс: {e}")
    
    # Вызываем оригинальный обработчик
    await learning.start_learning(callback, db, user_id, state)

async def wrapped_next_section(callback: types.CallbackQuery):
    """Переход к следующему разделу с отслеживанием прогресса"""
    db = _components['database']
    user_id = callback.from_user.id
    
    # Получаем текущий номер урока из БД обучения
    current_lesson = db.get_user_progress(user_id)
    
    if current_lesson:
        # current_lesson может быть tuple или int, извлекаем число
        if isinstance(current_lesson, tuple):
            lesson_num = current_lesson[0]  # Берем первый элемент
        else:
            lesson_num = current_lesson
        
        # Отмечаем предыдущий урок как завершенный
        try:
            await complete_lesson_tracking(
                callback, 
                'prompt_engineering',  # или получаем из state
                lesson_num
            )
        except Exception as e:
            # Логируем ошибку, но продолжаем работу
            logger.error(f"Ошибка отслеживания прогресса: {e}")
    
    # Вызываем оригинальный обработчик
    await learning.next_section(callback, db, user_id)

async def wrapped_show_course_activity(callback: types.CallbackQuery, state: FSMContext):
    """Показать активность - ИСПРАВЛЕНО: полная версия со всеми уроками"""
    db = _components['database']
    # ИСПРАВЛЕНО: используем ПОЛНУЮ активность из learning.py со списком всех уроков
    await learning.show_course_activity(callback, db, callback.from_user.id, state)

# ============================================================================
# WRAPPER ФУНКЦИИ ДЛЯ ОСТАЛЬНЫХ ОБРАБОТЧИКОВ
# ============================================================================

async def _show_course_program(c, state: FSMContext):
    db = _components['database']
    await learning.show_course_program(c, db, state)

async def _restart_course(c):
    db = _components['database']
    await learning.restart_course(c, db, c.from_user.id)

async def _go_to_lesson(c):
    db = _components['database']
    await learning.go_to_lesson(c, db, c.from_user.id)

async def _show_lesson_list(c, state: FSMContext):
    await learning.show_lesson_list(c, state)

async def _show_course_program_vibe(c):
    await learning.show_course_program_vibe(c)

async def _show_course_activity_vibe(c):
    await learning.show_course_activity_vibe(c)

async def _show_vibe_conditions(c):
    await learning.show_vibe_conditions(c)

async def _show_course_program_web(c):
    await learning.show_course_program_web(c)

async def _show_course_activity_web(c):
    await learning.show_course_activity_web(c)

async def _show_web_conditions(c):
    await learning.show_web_conditions(c)

# ============================================================================
# WRAPPER ФУНКЦИИ ДЛЯ ТРЕНАЖЕРА
# ============================================================================

async def _set_trainer(c):
    await trainer.set_trainer_mode(c, c.from_user.id)

# ============================================================================
# WRAPPER ФУНКЦИИ ДЛЯ КОНСУЛЬТАНТА
# ============================================================================

async def _set_consultant(c):
    await consultant.set_consultant_mode(c, c.from_user.id)

# ============================================================================
# WRAPPER ФУНКЦИИ ДЛЯ ТЕСТИРОВАНИЯ
# ============================================================================

async def _start_test(c):
    db = _components['database']
    await testing.start_test(c, db, c.from_user.id)

async def _next_test_question(c):
    await testing.next_test_question(c, c.from_user.id)

async def _show_test_result(c):
    db = _components['database']
    await testing.show_test_result(c, db, c.from_user.id)

async def _retry_test(c):
    await testing.retry_test(c, c.from_user.id)

async def _retake_lesson(c):
    db = _components['database']
    await testing.retake_lesson(c, db, c.from_user.id)

async def _complete_lesson_after_test(c):
    db = _components['database']
    user_id = c.from_user.id
    
    # Получаем текущий урок
    current_lesson = db.get_user_progress(user_id)
    
    if current_lesson:
        # current_lesson может быть tuple или int, извлекаем число
        if isinstance(current_lesson, tuple):
            lesson_num = current_lesson[0]
        else:
            lesson_num = current_lesson
        
        # Отмечаем урок как завершенный в системе прогресса
        try:
            await complete_lesson_tracking(c, 'prompt_engineering', lesson_num)
        except Exception as e:
            logger.error(f"Ошибка отслеживания прогресса: {e}")
    
    # Вызываем оригинальный обработчик
    await testing.complete_lesson_after_test(c, db, user_id)

# ============================================================================
# WRAPPER ФУНКЦИИ ДЛЯ НАВИГАТОРА
# ============================================================================

async def _nav_text_list(c):
    db = _components['database']
    await navigator.nav_text_list(c, db)

async def _nav_image_list(c):
    db = _components['database']
    await navigator.nav_image_list(c, db)

async def _nav_video_list(c):
    db = _components['database']
    await navigator.nav_video_list(c, db)

# ============================================================================
# WRAPPER ДЛЯ АДМИН-ПАНЕЛИ (ИСПРАВЛЕННАЯ ВЕРСИЯ)
# ============================================================================

async def wrapped_admin_command(message: types.Message):
    """Wrapper для команды /admin (aiogram) - ИСПРАВЛЕНО"""
    # Вызываем обработчик админки напрямую с aiogram message
    await admin_command(message)

async def wrapped_admin_callback(callback: types.CallbackQuery):
    """Wrapper для callback админки (aiogram) - ИСПРАВЛЕНО"""
    # Вызываем напрямую с aiogram callback
    await handle_admin_callback(callback)

# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

async def main():
    """Главная функция запуска бота"""
    
    # Проверка токена
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
        sys.exit(1)
    
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК БОТА 'ИИ ИНЖЕНЕР'")
    logger.info("=" * 50)
    
    # Инициализация компонентов
    success = await init_components()
    if not success:
        logger.error("❌ Не удалось инициализировать компоненты")
        sys.exit(1)
    
    # Создание бота и диспетчера
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    
    # Регистрация middleware для автоматической регистрации пользователей
    dp.message.middleware(register_user_middleware)
    dp.callback_query.middleware(register_user_middleware)
    
    db = _components['database']
    
    logger.info("📋 Регистрация обработчиков...")
    
    # ========================================================================
    # ПОДКЛЮЧАЕМ РОУТЕР MENU
    # ========================================================================
    
    dp.include_router(menu.router)
    
    # ========================================================================
    # КОМАНДЫ
    # ========================================================================
    
    dp.message.register(menu.cmd_start, Command("start"))
    dp.message.register(wrapped_admin_command, Command("admin"))  # ИСПРАВЛЕНО
    
    # ========================================================================
    # АДМИН-ПАНЕЛЬ (ИСПРАВЛЕННЫЕ ОБРАБОТЧИКИ)
    # ========================================================================
    
    dp.callback_query.register(
        wrapped_admin_callback,  # ИСПРАВЛЕНО
        F.data.startswith("admin_")
    )
    
    # ========================================================================
    # АКТИВНОСТЬ ПОЛЬЗОВАТЕЛЯ (НОВЫЙ ОБРАБОТЧИК)
    # ========================================================================
    
    dp.callback_query.register(
        show_user_activity,
        F.data == "user_activity"
    )
    
    # ========================================================================
    # РЕЖИМЫ
    # ========================================================================
    
    dp.callback_query.register(wrapped_start_learning, F.data == "mode_learning")
    dp.callback_query.register(_set_trainer, F.data == "mode_trainer")
    dp.callback_query.register(navigator.show_navigator, F.data == "mode_navigator")
    dp.callback_query.register(_set_consultant, F.data == "mode_consultant")
    
    # ========================================================================
    # ОБУЧЕНИЕ
    # ========================================================================
    
    dp.callback_query.register(wrapped_next_section, F.data == "next_section")
    dp.callback_query.register(_show_lesson_list, F.data == "lesson_list")
    dp.callback_query.register(_show_course_program, F.data == "course_program")
    dp.callback_query.register(wrapped_show_course_activity, F.data == "course_activity")
    dp.callback_query.register(_restart_course, F.data == "restart_course")
    dp.callback_query.register(_go_to_lesson, F.data.startswith("goto_"))
    dp.callback_query.register(learning.locked_lesson, F.data.startswith("locked_"))
    dp.callback_query.register(learning.module_info, F.data.startswith("module_info_"))
    
    # Vibe Coding
    dp.callback_query.register(_show_course_program_vibe, F.data == "course_program_vibe")
    dp.callback_query.register(_show_course_activity_vibe, F.data == "course_activity_vibe")
    dp.callback_query.register(_show_vibe_conditions, F.data == "vibe_conditions")

    # Веб-приложения на ИИ
    dp.callback_query.register(_show_course_program_web, F.data == "course_program_web")
    dp.callback_query.register(_show_course_activity_web, F.data == "course_activity_web")
    dp.callback_query.register(_show_web_conditions, F.data == "web_conditions")
    
    # ========================================================================
    # ТЕСТИРОВАНИЕ
    # ========================================================================
    
    dp.callback_query.register(_start_test, F.data == "start_test")
    dp.callback_query.register(_next_test_question, F.data == "next_test_question")
    dp.callback_query.register(_show_test_result, F.data == "show_test_result")
    dp.callback_query.register(_retry_test, F.data == "retry_test")
    dp.callback_query.register(_retake_lesson, F.data == "retake_lesson")
    dp.callback_query.register(_complete_lesson_after_test, F.data == "complete_lesson_after_test")
    
    # ========================================================================
    # НАВИГАТОР - КАТЕГОРИИ
    # ========================================================================
    
    dp.callback_query.register(navigator.nav_text, F.data == "nav_text")
    dp.callback_query.register(navigator.nav_image, F.data == "nav_image")
    dp.callback_query.register(navigator.nav_video, F.data == "nav_video")
    
    # ========================================================================
    # НАВИГАТОР - ТЕКСТОВЫЕ ИИ
    # ========================================================================
    
    dp.callback_query.register(_nav_text_list, F.data == "nav_text_list")
    dp.callback_query.register(navigator.nav_text_compare, F.data == "nav_text_compare")
    dp.callback_query.register(navigator.nav_text_tactics, F.data == "nav_text_tactics")
    dp.callback_query.register(navigator.nav_text_lifehacks, F.data == "nav_text_lifehacks")
    dp.callback_query.register(navigator.nav_text_pitfalls, F.data == "nav_text_pitfalls")
    dp.callback_query.register(navigator.nav_text_cheatsheet, F.data == "nav_text_cheatsheet")
    
    # ========================================================================
    # НАВИГАТОР - ИЗОБРАЖЕНИЯ
    # ========================================================================
    
    dp.callback_query.register(_nav_image_list, F.data == "nav_image_list")
    dp.callback_query.register(navigator.nav_image_compare, F.data == "nav_image_compare")
    dp.callback_query.register(navigator.nav_image_tactics, F.data == "nav_image_tactics")
    dp.callback_query.register(navigator.nav_image_lifehacks, F.data == "nav_image_lifehacks")
    dp.callback_query.register(navigator.nav_image_pitfalls, F.data == "nav_image_pitfalls")
    dp.callback_query.register(navigator.nav_image_cheatsheet, F.data == "nav_image_cheatsheet")
    
    # ========================================================================
    # НАВИГАТОР - ВИДЕО
    # ========================================================================
    
    dp.callback_query.register(_nav_video_list, F.data == "nav_video_list")
    dp.callback_query.register(navigator.nav_video_compare, F.data == "nav_video_compare")
    dp.callback_query.register(navigator.nav_video_tactics, F.data == "nav_video_tactics")
    dp.callback_query.register(navigator.nav_video_lifehacks, F.data == "nav_video_lifehacks")
    
    # ========================================================================
    # ТЕКСТОВЫЕ СООБЩЕНИЯ
    # ========================================================================
    
    dp.message.register(handle_text_message)
    
    # ========================================================================
    # УСТАНОВКА КОМАНД БОТА
    # ========================================================================
    
    # КРИТИЧНО: Сначала удаляем все старые команды
    await bot.delete_my_commands()
    logger.info("🗑️ Старые команды удалены")
    
    # Устанавливаем команды для всех пользователей (default scope)
    from aiogram.types import BotCommandScopeDefault
    user_commands = [
        BotCommand(command="start", description="🏠 Главное меню")
    ]
    
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
    logger.info("✅ Команды для пользователей установлены")
    
    # Для админов добавляем /admin через chat scope (перекрывает default)
    from aiogram.types import BotCommandScopeChat
    admin_commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="admin", description="⚙️ Админ-панель")
    ]
    
    # Список ID админов
    admin_ids = [1501905373, 307782709]
    
    for admin_id in admin_ids:
        try:
            await bot.set_my_commands(
                admin_commands,
                scope=BotCommandScopeChat(chat_id=admin_id)
            )
            logger.info(f"✅ Команды админа установлены (ID: {admin_id})")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось установить команды для админа {admin_id}: {e}")
    
    # ========================================================================
    # ЗАПУСК POLLING
    # ========================================================================
    
    logger.info("=" * 50)
    logger.info("✅ БОТ УСПЕШНО ЗАПУЩЕН!")
    logger.info("=" * 50)
    logger.info("📊 Система отслеживания прогресса: АКТИВНА")
    logger.info("⚙️ Админ-панель: ДОСТУПНА")
    logger.info("🔐 Админы: 1501905373, 307782709")
    logger.info("=" * 50)
    
    await dp.start_polling(bot)

# ============================================================================
# ТОЧКА ВХОДА
# ============================================================================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 50)
        logger.info("👋 БОТ ОСТАНОВЛЕН ПОЛЬЗОВАТЕЛЕМ")
        logger.info("=" * 50)
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}", exc_info=True)
        sys.exit(1)