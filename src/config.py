import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Claude AI
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
CLAUDE_ENDPOINT = os.getenv('CLAUDE_ENDPOINT', 'https://api.vsegpt.ru/v1/chat/completions')
CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'anthropic/claude-sonnet-4.5-1m-thinking')

# Яндекс.Диск
YADISK_PUBLIC_URL = os.getenv('YADISK_PUBLIC_URL')

# Администраторы
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]

# Пути (для работы с persistenceMount на Amvera)
PERSISTENCE_PATH = os.getenv('PERSISTENCE_PATH', 'data')
KB_PATH = os.path.join(PERSISTENCE_PATH, 'knowledge_base')
DB_PATH = os.path.join(PERSISTENCE_PATH, 'bot.db')
LOG_PATH = 'logs/bot.log'

# Логирование
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Создание директорий
os.makedirs(KB_PATH, exist_ok=True)
os.makedirs('logs', exist_ok=True)