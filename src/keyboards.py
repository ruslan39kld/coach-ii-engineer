from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню"""
    keyboard = [
        [KeyboardButton(text="🔍 Задать вопрос")],
        [KeyboardButton(text="📚 Категории"), KeyboardButton(text="❓ Частые вопросы")],
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="ℹ️ О боте")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )

def get_categories_menu() -> ReplyKeyboardMarkup:
    """Меню категорий"""
    keyboard = [
        [KeyboardButton(text="📋 План-график и ПЗ")],
        [KeyboardButton(text="🏪 Проведение закупок")],
        [KeyboardButton(text="📝 Работа с документами")],
        [KeyboardButton(text="🔧 Технические вопросы")],
        [KeyboardButton(text="📜 Регламенты")],
        [KeyboardButton(text="🏠 Главное меню")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

def get_back_button() -> ReplyKeyboardMarkup:
    """Кнопка назад"""
    keyboard = [[KeyboardButton(text="🏠 Главное меню")]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_inline_main_menu() -> InlineKeyboardMarkup:
    """Инлайн главное меню"""
    keyboard = [
        [InlineKeyboardButton("📚 Категории", callback_data="categories")],
        [InlineKeyboardButton("📝 Работа с документами", callback_data="documents")],
        [InlineKeyboardButton("📋 План-график и ПЗ", callback_data="schedule")],
        [InlineKeyboardButton("🏪 Как оформить закупку", callback_data="purchase")],
        [InlineKeyboardButton("🔧 Технические вопросы", callback_data="technical")],
        [InlineKeyboardButton("💡 Что ты можешь?", callback_data="capabilities")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_inline_categories_menu() -> InlineKeyboardMarkup:
    """Инлайн меню категорий"""
    keyboard = [
        [InlineKeyboardButton("📋 План-график и ПЗ", callback_data="cat_schedule")],
        [InlineKeyboardButton("🏪 Проведение закупок", callback_data="cat_purchases")],
        [InlineKeyboardButton("📝 Работа с документами", callback_data="cat_documents")],
        [InlineKeyboardButton("🔧 Технические вопросы", callback_data="cat_technical")],
        [InlineKeyboardButton("📜 Регламенты", callback_data="cat_regulations")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_inline_back_button() -> InlineKeyboardMarkup:
    """Инлайн кнопка назад"""
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)