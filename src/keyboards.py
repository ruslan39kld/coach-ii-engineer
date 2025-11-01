from telegram import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu() -> ReplyKeyboardMarkup:
    """Только кнопка Меню"""
    keyboard = [
        [KeyboardButton(text="🔄 Меню")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Задайте ваш вопрос..."
    )