"""
Telegram-бот для поиска земельных участков
"""
import sys
from pathlib import Path
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database import Database

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
PRICE, SQUARE, DISTRICT = range(3)


class EasuzBot:
    def __init__(self, token: str):
        self.token = token
        self.db = Database()
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        keyboard = [
            [InlineKeyboardButton("🔍 Поиск по цене", callback_data='search_price')],
            [InlineKeyboardButton("📐 Поиск по площади", callback_data='search_square')],
            [InlineKeyboardButton("📍 Поиск по району", callback_data='search_district')],
            [InlineKeyboardButton("📊 Статистика", callback_data='stats')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = (
            "🌍 <b>Бот поиска земельных участков ЕАСУЗ</b>\n\n"
            "Здесь вы можете найти участки:\n"
            "• По цене\n"
            "• По площади\n"
            "• По району\n\n"
            "Выберите действие:"
        )
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = (
            "📖 <b>Справка</b>\n\n"
            "<b>Команды:</b>\n"
            "/start - Главное меню\n"
            "/help - Эта справка\n"
            "/stats - Статистика базы\n\n"
            "<b>Поиск:</b>\n"
            "• По цене - найти участки до указанной суммы\n"
            "• По площади - найти участки нужного размера\n"
            "• По району - найти в конкретном районе\n\n"
            "📊 База обновлена: 01.11.2025\n"
            "📦 Всего объявлений: 3110"
        )
        
        await update.message.reply_text(help_text, parse_mode='HTML')
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /stats"""
        stats = self.db.get_stats()
        
        stats_text = (
            "📊 <b>Статистика базы данных</b>\n\n"
            f"📦 Всего объявлений: <b>{stats['total']}</b>\n"
            f"✅ Активных: <b>{stats['active']}</b>\n"
            f"📅 Последнее обновление: 01.11.2025\n\n"
            "Используйте /start для поиска участков"
        )
        
        await update.message.reply_text(stats_text, parse_mode='HTML')
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'stats':
            stats = self.db.get_stats()
            stats_text = (
                "📊 <b>Статистика базы данных</b>\n\n"
                f"📦 Всего объявлений: <b>{stats['total']}</b>\n"
                f"✅ Активных: <b>{stats['active']}</b>\n"
                f"📅 Последнее обновление: 01.11.2025"
            )
            await query.edit_message_text(stats_text, parse_mode='HTML')
            
        elif query.data == 'search_price':
            await query.edit_message_text(
                "💰 Введите максимальную цену (например: 1000000):",
                parse_mode='HTML'
            )
            return PRICE
            
        elif query.data == 'search_square':
            await query.edit_message_text(
                "📐 Введите минимальную площадь в кв.м (например: 1000):",
                parse_mode='HTML'
            )
            return SQUARE
            
        elif query.data == 'search_district':
            await query.edit_message_text(
                "📍 Введите название района (например: Мытищи):",
                parse_mode='HTML'
            )
            return DISTRICT
    
    def run(self):
        """Запуск бота"""
        application = Application.builder().token(self.token).build()
        
        # Регистрация обработчиков
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        application.add_handler(CallbackQueryHandler(self.button_callback))
        
        logger.info("🤖 Бот запущен!")
        application.run_polling()


def main():
    try:
        from config import BOT_TOKEN
        
        if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            raise ValueError("Токен не установлен")
            
    except ImportError:
        print("❌ ОШИБКА: Файл config.py не найден!")
        print("\n📝 Создайте файл config.py в корне проекта:")
        print("=" * 60)
        print('BOT_TOKEN = "ваш_токен_от_BotFather"')
        print("=" * 60)
        print("\n📖 Как получить токен:")
        print("1. Откройте @BotFather в Telegram")
        print("2. Отправьте /newbot")
        print("3. Следуйте инструкциям")
        print("4. Скопируйте токен в config.py")
        return
    except ValueError:
        print("❌ ОШИБКА: Установите токен в config.py!")
        print("Замените YOUR_BOT_TOKEN_HERE на реальный токен")
        return
    
    bot = EasuzBot(BOT_TOKEN)
    bot.run()


if __name__ == "__main__":
    main()