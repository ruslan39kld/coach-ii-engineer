from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)
from telegram.error import BadRequest
import logging
from datetime import datetime
import config

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start"""
    # Создаем кнопку "Меню" — только один раз, под приветствием
    keyboard = [[InlineKeyboardButton("Меню", callback_data="menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 Добрый день!\n\n"
        "Я — AI-консультант по системе ЕАСУЗ 44-ФЗ.\n\n"
        "Помогу разобраться с:\n"
        "• Процедурами закупок\n"
        "• Заполнением форм и блоков\n"
        "• Требованиями к документации\n"
        "• Работой с модулями системы\n"
        "• Типовыми ошибками\n\n"
        "Чем могу Вам помочь?",
        reply_markup=reply_markup  # Только здесь добавляем кнопку
    )

async def handle_what_can_you_do(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ответ на вопрос 'Что ты можешь?'"""
    await update.message.reply_text(
        "💡 Я — AI-ассистент по системе ЕАСУЗ 44-ФЗ.\n\n"
        "Мои возможности:\n"
        "✅ Отвечаю на вопросы по работе с системой\n"
        "✅ Помогаю с заполнением форм и документов\n"
        "✅ Объясняю процедуры и регламенты\n"
        "✅ Подсказываю решения типовых проблем\n"
        "✅ Работаю на базе актуальной документации\n\n"
        "База знаний включает:\n"
        "📚 Инструкции и регламенты\n"
        "📄 Методические материалы\n"
        "🛠️ Решения технических вопросов\n"
        "📝 Примеры заполнения форм\n\n"
        "Чем могу Вам помочь?",
        reply_markup=None  # Без кнопки
    )

async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатия на кнопку 'Меню'"""
    query = update.callback_query
    await query.answer()  # Отвечаем на callback
    
    # Имитируем команду /start
    await cmd_start(query.message, context)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка вопросов пользователя"""
    logging.info(f"[handle_text_message] User: {update.effective_user.id}, Question: {update.message.text}")
    
    text = update.message.text.strip().lower()
    if text in ["что ты можешь?", "что ты можешь"]:
        return  # Не обрабатываем здесь — обработано выше

    processing_msg = await update.message.reply_text("⏳ Обрабатываю запрос...")
    
    try:
        database = context.bot_data.get('database')
        claude_service = context.bot_data.get('claude_service')
        
        if not database or not claude_service:
            logging.error(f"[handle_text_message] Database or Claude not initialized!")
            await processing_msg.delete()
            await update.message.reply_text(
                "❌ Сервис временно недоступен. Попробуйте через минуту.",
                reply_markup=None
            )
            return
        
        # Получаем ответ от Claude
        answer, response_time = await claude_service.ask(update.message.text, database)
        
        logging.info(f"[handle_text_message] Response time: {response_time}ms")
        
        # Логируем запрос
        database.log_query(
            user_id=update.effective_user.id,
            username=update.effective_user.username or "",
            query=update.message.text,
            answer=answer,
            response_time_ms=response_time
        )
        
        # Удаляем сообщение "обрабатываю"
        try:
            await processing_msg.delete()
        except:
            pass
        
        # Отправляем ответ БЕЗ КНОПОК
        try:
            await update.message.reply_text(
                answer,
                reply_markup=None,  # Никаких кнопок
                parse_mode="Markdown"
            )
        except BadRequest as e:
            if "Can't parse entities" in str(e):
                logging.warning(f"[handle_text_message] Markdown error, sending without formatting")
                await update.message.reply_text(
                    answer,
                    reply_markup=None,
                    parse_mode=None
                )
            else:
                raise
        
    except Exception as e:
        logging.error(f"[handle_text_message] Error: {e}", exc_info=True)
        try:
            await processing_msg.delete()
        except:
            pass
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке запроса.\nПопробуйте переформулировать вопрос.",
            reply_markup=None
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
        f"📊 СТАТИСТИКА:\n\n"
        f"📚 Документов: {stats['documents']}\n"
        f"📝 Запросов: {stats['queries']}\n"
        f"👥 Пользователей: {stats['users']}"
    )

def register_handlers(application: Application) -> None:
    """Регистрация всех обработчиков"""
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("reload", reload_kb))
    application.add_handler(CommandHandler("stats_admin", admin_stats))

    # Обработчик "Что ты можешь?"
    what_filter = filters.Regex(r"^(?i)(что ты можешь\??)$")
    application.add_handler(MessageHandler(what_filter, handle_what_can_you_do))

    # Обработчик нажатия на кнопку "Меню"
    application.add_handler(CallbackQueryHandler(handle_menu_callback, pattern="menu"))

    # Обработчик всех прочих текстовых сообщений — должен быть последним!
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))