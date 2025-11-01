from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram.error import BadRequest
import logging
from datetime import datetime

import keyboards as kb
import config

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start"""
    await update.message.reply_text(
        "👋 Добрый день!\n\n"
        "Я — AI-консультант по системе ЕАСУЗ 44-ФЗ.\n\n"
        "Задайте ваш вопрос, и я предоставлю подробную инструкцию.",
        reply_markup=kb.get_main_menu()
    )

async def menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка кнопки Меню"""
    await cmd_start(update, context)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка вопросов пользователя"""
    logging.info(f"[handle_text_message] User: {update.effective_user.id}, Question: {update.message.text}")
    
    processing_msg = await update.message.reply_text("⏳ Обрабатываю запрос...")
    
    try:
        database = context.bot_data.get('database')
        claude_service = context.bot_data.get('claude_service')
        
        if not database or not claude_service:
            logging.error(f"[handle_text_message] Database or Claude not initialized!")
            await processing_msg.delete()
            await update.message.reply_text(
                "❌ Сервис временно недоступен. Попробуйте через минуту.",
                reply_markup=kb.get_main_menu()
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
        
        # Отправляем ответ
        try:
            await update.message.reply_text(
                answer,
                reply_markup=kb.get_main_menu(),
                parse_mode="Markdown"
            )
        except BadRequest as e:
            if "Can't parse entities" in str(e):
                logging.warning(f"[handle_text_message] Markdown error, sending without formatting")
                await update.message.reply_text(
                    answer,
                    reply_markup=kb.get_main_menu(),
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
            reply_markup=kb.get_main_menu()
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
    
    application.add_handler(MessageHandler(filters.Regex("^🔄 Меню$"), menu_button))
    
    # Обработчик всех текстовых сообщений (вопросов) - должен быть последним!
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))