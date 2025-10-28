from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from telegram.error import BadRequest
import logging
from datetime import datetime
import re

import keyboards as kb
import config

# FAQ КЭШИРОВАНИЕ для быстрых ответов
FAQ_CACHE = {
    "что такое еасуз": "ЕАСУЗ (Единая автоматизированная система управления закупками) — это информационная система для управления закупками по 44-ФЗ.",
    "как создать план-график": "Для создания плана-графика перейдите в раздел 'План-график' → 'Создать новый' → заполните обязательные поля → сохраните.",
    "как оформить закупку": "1. Создайте позицию в плане-графике\n2. Заполните извещение\n3. Прикрепите документацию\n4. Опубликуйте извещение",
    "что ты можешь": "Я помогаю с работой в системе ЕАСУЗ: отвечаю на вопросы по процедурам, помогаю с заполнением форм, объясняю требования к документации.",
}

# Состояния для ConversationHandler
WAITING_FOR_QUERY = 0

def escape_markdown_v2(text: str) -> str:
    """
    Экранирует специальные символы для Markdown V2.
    Используется для безопасной отправки текста в Telegram.
    """
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def clean_markdown(text: str) -> str:
    """
    Очищает текст от некорректной Markdown-разметки.
    Заменяет потенциально проблемные символы.
    """
    # Убираем одиночные * и _ которые могут быть не закрыты
    text = re.sub(r'(?<!\*)\*(?!\*)', '', text)  # Удаляем одиночные *
    text = re.sub(r'(?<!_)_(?!_)', '', text)      # Удаляем одиночные _
    
    # Убираем незакрытые скобки в ссылках
    text = re.sub(r'\[([^\]]+)$', r'\1', text)    # Незакрытая [
    text = re.sub(r'\(([^\)]+)$', r'\1', text)    # Незакрытая (
    
    return text

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Команда /start"""
    await update.message.reply_text(
        "👋 **Добрый день!**\n\n"
        "Я — AI-консультант по системе **ЕАСУЗ 44-ФЗ**.\n\n"
        "Помогу разобраться с:\n"
        "• Процедурами закупок\n"
        "• Заполнением форм и блоков\n"
        "• Требованиями к документации\n"
        "• Работой с модулями системы\n"
        "• Типовыми ошибками\n\n"
        "Выберите действие ниже 👇",
        reply_markup=kb.get_inline_main_menu(),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало диалога"""
    await update.message.reply_text(
        "📝 **Введите ваш вопрос:**\n\n"
        "_Например:_\n"
        "• Как заполнить блок Кандидатуры?\n"
        "• Сроки продления электронного аукциона\n"
        "• Как работать с РХО?",
        reply_markup=kb.get_back_button(),
        parse_mode="Markdown"
    )
    return WAITING_FOR_QUERY

async def process_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка вопроса пользователя"""
    processing_msg = await update.message.reply_text("⏳ Обрабатываю запрос...")
    
    try:
        # Получаем зависимости из bot_data
        database = context.bot_data['database']
        claude_service = context.bot_data['claude_service']
        
        # Получаем ответ от Claude
        answer, response_time = await claude_service.ask(update.message.text, database)
        
        # Логируем запрос
        database.log_query(
            user_id=update.effective_user.id,
            username=update.effective_user.username or "",
            query=update.message.text,
            answer=answer,
            response_time_ms=response_time
        )
        
        # Удаляем сообщение "обрабатываю"
        await processing_msg.delete()
        
        # Отправляем ответ с обработкой ошибок Markdown
        try:
            # Сначала пробуем с Markdown
            await update.message.reply_text(
                answer,
                reply_markup=kb.get_main_menu(),
                parse_mode="HTML"
            )
        except BadRequest as e:
            if "Can't parse entities" in str(e):
                # Если ошибка парсинга - отправляем без форматирования
                logging.warning(f"Markdown parsing error, sending without formatting: {e}")
                await update.message.reply_text(
                    answer,
                    reply_markup=kb.get_main_menu(),
                    parse_mode=None
                )
            else:
                raise
        
    except Exception as e:
        logging.error(f"Error processing query: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка. Попробуйте еще раз или обратитесь в поддержку.",
            reply_markup=kb.get_main_menu()
        )
    
    return ConversationHandler.END

async def categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показ категорий"""
    await update.message.reply_text(
        "📚 **Выберите категорию:**",
        reply_markup=kb.get_categories_menu(),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Частые вопросы"""
    faq_text = """❓ **ЧАСТЫЕ ВОПРОСЫ:**

1️⃣ Как заполнить блок Кандидатуры?
2️⃣ Как работать с РХО?
3️⃣ Сроки продления при изменениях
4️⃣ Схема 223-44-223
5️⃣ Внесение изменений в закупку

_Для получения ответа просто напишите номер вопроса или его текст._
"""
    await update.message.reply_text(faq_text, parse_mode="Markdown")
    return ConversationHandler.END

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Статистика бота"""
    database = context.bot_data['database']
    stats_data = database.get_stats()
    
    stats_text = f"""📊 **СТАТИСТИКА БОТА:**

❓ Вопросов в FAQ: **{stats_data.get('faq', 0)}**
📚 Документов в базе: **{stats_data['documents']}**
📝 Обработано запросов: **{stats_data['queries']}**
👥 Всего пользователей: **{stats_data['users']}**

_База знаний обновляется автоматически при запуске бота._
"""
    await update.message.reply_text(stats_text, parse_mode="Markdown")
    return ConversationHandler.END

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """О боте"""
    about_text = """ℹ️ **О БОТЕ:**

🤖 **ЕАСУЗ 44-ФЗ Ассистент**
Версия: 1.0

AI-консультант по работе с системой ЕАСУЗ на основе Claude AI.

📚 База знаний: Яндекс.Диск
🧠 AI: Claude Sonnet 4.5
⚡ Всегда актуальная информация

Разработано для специалистов контрактных служб.
"""
    await update.message.reply_text(about_text, parse_mode="Markdown")
    return ConversationHandler.END

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Возврат в главное меню"""
    await update.message.reply_text(
        "🏠 Главное меню:",
        reply_markup=kb.get_main_menu()
    )
    return ConversationHandler.END

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка любых текстовых сообщений (вопросов пользователя)"""
    logging.info(f"[handle_text_message] Вызвана функция. User: {update.effective_user.id}, Time: {datetime.now()}")
    
    # Игнорируем команды меню
    if update.message.text in ["🔍 Задать вопрос", "📚 Категории", "❓ Частые вопросы", 
                                "📊 Статистика", "ℹ️ О боте", "🏠 Главное меню"]:
        logging.info(f"[handle_text_message] Игнорируем команду меню: {update.message.text}")
        return
    
    user_question = update.message.text
    logging.info(f"[handle_text_message] Получен вопрос от {update.effective_user.id}: {user_question}")
    
    # ПРОВЕРКА FAQ КЭША для быстрых ответов
    question_lower = user_question.lower().strip()
    if question_lower in FAQ_CACHE:
        logging.info(f"[handle_text_message] Найден ответ в FAQ кэше")
        await update.message.reply_text(
            FAQ_CACHE[question_lower],
            reply_markup=kb.get_inline_back_button()
        )
        return
    
    processing_msg = await update.message.reply_text("⏳ Обрабатываю запрос...")
    
    try:
        # Получаем зависимости из bot_data (БЕЗОПАСНО)
        database = context.bot_data.get('database')
        claude_service = context.bot_data.get('claude_service')
        
        if not database:
            logging.error(f"[handle_text_message] КРИТИЧЕСКАЯ ОШИБКА: database не инициализирована в bot_data!")
            logging.error(f"[handle_text_message] Доступные ключи в bot_data: {list(context.bot_data.keys())}")
            await update.message.reply_text(
                "❌ База данных не загружена.\n"
                "Бот перезагружается, попробуйте через минуту.",
                reply_markup=kb.get_inline_back_button()
            )
            return
        
        if not claude_service:
            logging.error(f"[handle_text_message] КРИТИЧЕСКАЯ ОШИБКА: claude_service не инициализирован!")
            await update.message.reply_text(
                "❌ Сервис AI не загружен.\n"
                "Попробуйте через минуту.",
                reply_markup=kb.get_inline_back_button()
            )
            return
        
        logging.info(f"[handle_text_message] Отправка запроса в Claude...")
        
        # Получаем ответ от Claude
        answer, response_time = await claude_service.ask(user_question, database)
        
        logging.info(f"[handle_text_message] Ответ получен за {response_time}ms")
        
        # Логируем запрос
        database.log_query(
            user_id=update.effective_user.id,
            username=update.effective_user.username or "",
            query=user_question,
            answer=answer,
            response_time_ms=response_time
        )
        
        # Удаляем сообщение "обрабатываю"
        try:
            await processing_msg.delete()
        except:
            pass
        
        # ИСПРАВЛЕНИЕ: Отправляем ответ с обработкой ошибок Markdown
        try:
            # Сначала пробуем отправить с Markdown
            await update.message.reply_text(
                answer,
                reply_markup=kb.get_inline_back_button(),
                parse_mode="Markdown"
            )
            logging.info(f"[handle_text_message] Ответ отправлен пользователю {update.effective_user.id}")
            
        except BadRequest as e:
            if "Can't parse entities" in str(e):
                # Если ошибка парсинга Markdown - отправляем без форматирования
                logging.warning(f"[handle_text_message] Ошибка Markdown парсинга: {e}")
                logging.warning(f"[handle_text_message] Отправляю ответ без форматирования")
                
                await update.message.reply_text(
                    answer,
                    reply_markup=kb.get_inline_back_button(),
                    parse_mode=None  # Без форматирования
                )
                logging.info(f"[handle_text_message] Ответ отправлен без форматирования пользователю {update.effective_user.id}")
            else:
                # Если другая ошибка - пробрасываем дальше
                raise
        
    except Exception as e:
        logging.error(f"[handle_text_message] Ошибка: {e}", exc_info=True)
        try:
            await processing_msg.delete()
        except:
            pass
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке запроса.\n"
            "Попробуйте переформулировать вопрос или используйте кнопки меню.",
            reply_markup=kb.get_inline_back_button()
        )

async def reload_kb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Перезагрузка базы знаний (только для админов)"""
    if update.effective_user.id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    yadisk_loader = context.bot_data['yadisk_loader']
    knowledge_base = context.bot_data['knowledge_base']
    
    await update.message.reply_text("⏳ Обновление базы знаний...")
    
    if yadisk_loader.download_all():
        knowledge_base.load_all_files()
        await update.message.reply_text("✅ База знаний обновлена!")
    else:
        await update.message.reply_text("❌ Ошибка обновления")

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Расширенная статистика для админов"""
    if update.effective_user.id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    database = context.bot_data['database']
    stats = database.get_stats()
    
    await update.message.reply_text(
        f"📊 **АДМИН СТАТИСТИКА:**\n\n"
        f"❓ FAQ вопросов: {stats.get('faq', 0)}\n"
        f"📚 Документов: {stats['documents']}\n"
        f"📝 Запросов: {stats['queries']}\n"
        f"👥 Пользователей: {stats['users']}",
        parse_mode="Markdown"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатий на инлайн-кнопки"""
    query = update.callback_query
    callback_data = query.data
    
    logging.info(f"[button_callback] Callback data: {callback_data}, User: {query.from_user.id}, Time: {datetime.now()}")
    
    try:
        # ВАЖНО: answer() должен быть вызван первым
        await query.answer()
        logging.info(f"[button_callback] query.answer() успешно выполнен")
    except Exception as e:
        logging.warning(f"[button_callback] Не удалось ответить на callback (возможно устарел): {e}")
    
    try:
        # Главное меню
        if callback_data == "main_menu":
            logging.info(f"[button_callback] Обработка: main_menu")
            await query.edit_message_text(
                "🏠 **Главное меню**\n\nВыберите действие:",
                reply_markup=kb.get_inline_main_menu(),
                parse_mode="Markdown"
            )
            logging.info(f"[button_callback] main_menu успешно обработан")
        
        # Категории
        elif callback_data == "categories":
            logging.info(f"[button_callback] Обработка: categories")
            await query.edit_message_text(
                "📚 **Категории вопросов:**\n\nВыберите интересующую категорию:",
                reply_markup=kb.get_inline_categories_menu(),
                parse_mode="Markdown"
            )
            logging.info(f"[button_callback] categories успешно обработан")
        
        # Работа с документами
        elif callback_data == "documents":
            await query.edit_message_text(
                "📝 **Работа с документами**\n\n"
                "Здесь вы можете узнать:\n"
                "• Как заполнять формы и блоки\n"
                "• Требования к документации\n"
                "• Шаблоны документов\n"
                "• Проверка документов\n\n"
                "_Задайте свой вопрос или выберите категорию_",
                reply_markup=kb.get_inline_back_button(),
                parse_mode="Markdown"
            )
        
        # План-график и ПЗ
        elif callback_data == "schedule":
            await query.edit_message_text(
                "📋 **План-график и ПЗ**\n\n"
                "Информация по:\n"
                "• Формированию плана-графика\n"
                "• Позициям закупок (ПЗ)\n"
                "• Срокам и изменениям\n"
                "• Согласованию и утверждению\n\n"
                "_Задайте свой вопрос_",
                reply_markup=kb.get_inline_back_button(),
                parse_mode="Markdown"
            )
        
        # Как оформить закупку
        elif callback_data == "purchase":
            await query.edit_message_text(
                "🏪 **Как оформить закупку**\n\n"
                "Пошаговая инструкция:\n"
                "• Создание закупки\n"
                "• Заполнение обязательных полей\n"
                "• Прикрепление документов\n"
                "• Публикация и мониторинг\n\n"
                "_Задайте конкретный вопрос_",
                reply_markup=kb.get_inline_back_button(),
                parse_mode="Markdown"
            )
        
        # Технические вопросы
        elif callback_data == "technical":
            await query.edit_message_text(
                "🔧 **Технические вопросы**\n\n"
                "Помощь по:\n"
                "• Работе с интерфейсом системы\n"
                "• Ошибкам и их решению\n"
                "• Настройкам и доступам\n"
                "• Интеграциям\n\n"
                "_Опишите вашу проблему_",
                reply_markup=kb.get_inline_back_button(),
                parse_mode="Markdown"
            )
        
        # Что ты можешь
        elif callback_data == "capabilities":
            await query.edit_message_text(
                "💡 **Что я могу:**\n\n"
                "🤖 Я — AI-ассистент по системе ЕАСУЗ 44-ФЗ\n\n"
                "**Мои возможности:**\n"
                "✅ Отвечаю на вопросы по работе с системой\n"
                "✅ Помогаю с заполнением форм и документов\n"
                "✅ Объясняю процедуры и регламенты\n"
                "✅ Подсказываю решения типовых проблем\n"
                "✅ Работаю на базе актуальной документации\n\n"
                "**База знаний включает:**\n"
                "📚 Инструкции и регламенты\n"
                "📋 Методические материалы\n"
                "🔧 Решения технических вопросов\n"
                "📝 Примеры заполнения форм\n\n"
                "_Просто задайте свой вопрос!_",
                reply_markup=kb.get_inline_back_button(),
                parse_mode="Markdown"
            )
        
        # Подкатегории
        elif callback_data == "cat_schedule":
            await query.edit_message_text(
                "📋 **План-график и ПЗ**\n\n_Задайте ваш вопрос по этой теме_",
                reply_markup=kb.get_inline_back_button(),
                parse_mode="Markdown"
            )
        elif callback_data == "cat_purchases":
            await query.edit_message_text(
                "🏪 **Проведение закупок**\n\n_Задайте ваш вопрос по этой теме_",
                reply_markup=kb.get_inline_back_button(),
                parse_mode="Markdown"
            )
        elif callback_data == "cat_documents":
            await query.edit_message_text(
                "📝 **Работа с документами**\n\n_Задайте ваш вопрос по этой теме_",
                reply_markup=kb.get_inline_back_button(),
                parse_mode="Markdown"
            )
        elif callback_data == "cat_technical":
            await query.edit_message_text(
                "🔧 **Технические вопросы**\n\n_Задайте ваш вопрос по этой теме_",
                reply_markup=kb.get_inline_back_button(),
                parse_mode="Markdown"
            )
        elif callback_data == "cat_regulations":
            await query.edit_message_text(
                "📜 **Регламенты**\n\n_Задайте ваш вопрос по этой теме_",
                reply_markup=kb.get_inline_back_button(),
                parse_mode="Markdown"
            )
        
        else:
            await query.edit_message_text(
                "❌ Неизвестная команда",
                reply_markup=kb.get_inline_back_button()
            )
    
    except Exception as e:
        logging.error(f"Ошибка в button_callback: {e}", exc_info=True)
        try:
            await query.message.reply_text(
                "❌ Произошла ошибка при обработке команды.\nПопробуйте /start",
                reply_markup=kb.get_inline_main_menu()
            )
        except:
            pass

def register_handlers(application: Application) -> None:
    """Регистрация всех обработчиков"""
    
    # ConversationHandler для диалога с вопросами
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🔍 Задать вопрос$"), ask_question)
        ],
        states={
            WAITING_FOR_QUERY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^🏠 Главное меню$"), process_query)
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^🏠 Главное меню$"), main_menu),
            CommandHandler("start", cmd_start)
        ],
    )
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("reload", reload_kb))
    application.add_handler(CommandHandler("stats_admin", admin_stats))
    
    # ВАЖНО: CallbackQueryHandler для обработки нажатий на инлайн-кнопки
    application.add_handler(CallbackQueryHandler(button_callback))
    
    application.add_handler(conv_handler)
    
    application.add_handler(MessageHandler(filters.Regex("^📚 Категории$"), categories))
    application.add_handler(MessageHandler(filters.Regex("^❓ Частые вопросы$"), faq))
    application.add_handler(MessageHandler(filters.Regex("^📊 Статистика$"), stats))
    application.add_handler(MessageHandler(filters.Regex("^ℹ️ О боте$"), about))
    application.add_handler(MessageHandler(filters.Regex("^🏠 Главное меню$"), main_menu))
    
    # ВАЖНО: Обработчик всех текстовых сообщений (вопросов) - должен быть последним!
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))