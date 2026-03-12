"""
Handlers package для бота ИИ Инженер
Включает все обработчики событий
"""

# Импорты существующих handlers
from . import menu
from . import learning
from . import testing
from . import trainer
from . import navigator
from . import consultant

# Импорты новых handlers для системы прогресса
from . import admin_handler
from . import progress_handler

__all__ = [
    'menu',
    'learning',
    'testing',
    'trainer',
    'navigator',
    'consultant',
    'admin_handler',
    'progress_handler'
]
