from aiogram import types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import sanitize_markdown

async def set_consultant_mode(callback: CallbackQuery, user_id: int):
    """Консультант"""
    from handlers.learning import user_modes
    
    user_modes[user_id] = "consultant"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(
        "💬 *Консультация по промт-инжинирингу*\n\n"
        "Готов ответить на вопросы по применению ИИ-инструментов в вашей работе.\n\n"
        "*Что можно спросить:*\n"
        "• Безопасность и конфиденциальность при использовании ИИ\n"
        "• Шаблоны и примеры эффективных промптов\n"
        "• Выбор подходящей нейросети для конкретной задачи\n\n"
        "Чем могу Вам помочь?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

async def handle_consultant_question(message: types.Message, db, claude_service, user_id: int):
    """Обработка вопроса в режиме консультанта"""
    text = message.text.strip()
    username = message.from_user.username
    
    msg = await message.answer("⏳ Ищу ответ...")
    
    try:
        answer, resp_time = await claude_service.ask(text, db, None)
        answer = sanitize_markdown(answer)
        
        db.log_query(user_id, username, text, answer, resp_time)
        
        await msg.delete()
        
        # Добавляем кнопку "Назад" к ответу
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
        
        await message.answer(answer, reply_markup=keyboard, parse_mode="Markdown")
        
    except Exception as e:
        import logging
        logging.error(f"Ошибка: {e}")
        await msg.delete()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
        
        await message.answer(
            "❌ Ошибка. Попробуйте позже.",
            reply_markup=keyboard
        )