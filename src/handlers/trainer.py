from aiogram import types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import sanitize_markdown

async def set_trainer_mode(callback: CallbackQuery, user_id: int):
    """Тренажер"""
    from handlers.learning import user_modes
    
    user_modes[user_id] = "trainer"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(
        "🛠 *Режим ТРЕНАЖЕР активирован*\n\n"
        "Отправьте мне ваш промпт, и я проанализирую его по формуле РЦК-ФОТ:\n"
        "• Роль\n"
        "• Цель\n"
        "• Контекст\n"
        "• Формат\n"
        "• Ограничения\n"
        "• Тон\n\n"
        "Жду ваш промпт!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

async def analyze_prompt(message: types.Message, claude_service, user_id: int):
    """Анализ промпта через Claude"""
    text = message.text.strip()
    
    msg = await message.answer("🔍 Анализирую промпт...")
    
    analysis = await claude_service.analyze_prompt(text)
    analysis = sanitize_markdown(analysis)
    
    await msg.delete()
    
    # Добавляем кнопку "Назад" к результату
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    
    await message.answer(analysis, reply_markup=keyboard, parse_mode="Markdown")