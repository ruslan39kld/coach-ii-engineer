"""
Адаптированный обработчик активности пользователя для aiogram
Отслеживание прогресса по курсам
"""

from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import sys
import os
from datetime import datetime

# Добавляем путь к базе данных (database на 2 уровня выше)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.db_manager import db


async def show_user_activity(callback: types.CallbackQuery):
    """Показать активность пользователя"""
    
    await callback.answer()
    
    user_id = callback.from_user.id
    user = callback.from_user
    
    # Регистрируем пользователя, если он новый
    db.register_user(
        user_id=user_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Получаем прогресс по всем курсам
    all_progress = db.get_all_user_progress(user_id)
    courses = db.get_all_courses()
    
    text = f"""
📊 <b>Твоя активность</b>

Привет, {user.first_name}! Вот твой прогресс по курсам:

"""
    
    has_activity = False
    
    for course in courses:
        progress = all_progress.get(course['course_slug'], {})
        
        completed = progress.get('completed', 0)
        total = progress.get('total', 0)
        percentage = progress.get('percentage', 0)
        is_finished = progress.get('is_finished', False)
        
        # Получаем дату начала обучения
        enrollment_date = db.get_enrollment_date(user_id, course['course_slug'])
        
        if enrollment_date:
            has_activity = True
            
            # Статус
            if is_finished:
                status_icon = "✅"
                status_text = "Завершен"
            elif completed > 0:
                status_icon = "⏸️"
                status_text = "В процессе"
            else:
                status_icon = "📝"
                status_text = "Начат"
            
            text += f"{status_icon} <b>{course['course_name']}</b>\n"
            text += f"├ Прогресс: {completed}/{total} уроков ({percentage}%)\n"
            text += f"├ Статус: {status_text}\n"
            
            # Дата начала
            if isinstance(enrollment_date, str):
                try:
                    date_obj = datetime.fromisoformat(enrollment_date)
                    formatted_date = date_obj.strftime("%d.%m.%Y")
                except:
                    formatted_date = enrollment_date
            else:
                formatted_date = str(enrollment_date)
            
            text += f"└ Дата начала: {formatted_date}\n"
            
            # Прогресс-бар
            total_bars = 10
            filled_bars = int(percentage / 10) if percentage > 0 else 0
            progress_bar = "█" * filled_bars + "░" * (total_bars - filled_bars)
            text += f"   {progress_bar}\n\n"
    
    if not has_activity:
        text += "Ты еще не начал обучение.\n"
        text += "Выбери курс в разделе 🎓 <b>Обучение</b>!"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ К курсам", callback_data='mode_learning')]
    ])
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )


async def start_course_tracking(callback: types.CallbackQuery, course_slug: str):
    """
    Записывает пользователя на курс
    Вызывается при первом нажатии на курс
    """
    
    user_id = callback.from_user.id
    user = callback.from_user
    
    # Регистрируем пользователя
    db.register_user(
        user_id=user_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Записываем на курс
    db.enroll_user(user_id, course_slug)
    
    # Логируем начало курса
    db.log_activity(user_id, 'course_started', course_slug)


async def complete_lesson_tracking(callback: types.CallbackQuery, course_slug: str, lesson_number: int):
    """
    Отмечает урок как пройденный
    
    Args:
        callback: Callback объект
        course_slug: Идентификатор курса (prompt_engineering, vibe_coding)
        lesson_number: Номер урока (1-23 или 1-20)
    """
    
    user_id = callback.from_user.id
    
    # Отмечаем урок как завершенный
    db.mark_lesson_completed(user_id, course_slug, lesson_number)
    
    # Проверяем, завершил ли пользователь весь курс
    progress = db.get_user_progress(user_id, course_slug)
    
    if progress['is_finished']:
        # Поздравляем с завершением курса!
        course = db.get_course_by_slug(course_slug)
        
        congrats_text = f"""
🎉 <b>Поздравляем!</b> 🎉

Ты завершил курс "<b>{course['course_name']}</b>"!

✅ Пройдено уроков: {progress['completed']}/{progress['total']}

Отличная работа! Теперь ты можешь применять полученные знания на практике.

Хочешь продолжить обучение? Выбери следующий курс!
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎓 Другие курсы", callback_data='mode_learning')],
            [InlineKeyboardButton(text="📊 Моя активность", callback_data='user_activity')]
        ])
        
        await callback.message.answer(
            congrats_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )


async def get_lesson_progress_text(user_id: int, course_slug: str) -> str:
    """
    Генерирует текст с прогрессом по урокам курса
    
    Returns:
        Отформатированный текст с прогрессом
    """
    
    progress = db.get_user_progress(user_id, course_slug)
    course = db.get_course_by_slug(course_slug)
    
    if not course:
        return ""
    
    text = f"\n📊 <b>Твой прогресс:</b> {progress['completed']}/{progress['total']} уроков"
    
    # Прогресс-бар
    total_bars = 10
    filled_bars = int(progress['percentage'] / 10) if progress['percentage'] > 0 else 0
    progress_bar = "█" * filled_bars + "░" * (total_bars - filled_bars)
    text += f"\n{progress_bar} {progress['percentage']}%\n"
    
    return text


async def track_lesson_view(callback: types.CallbackQuery, course_slug: str, lesson_number: int):
    """
    Отслеживает просмотр урока (не завершение!)
    Можно использовать для аналитики
    """
    
    user_id = callback.from_user.id
    
    db.log_activity(
        user_id,
        'lesson_viewed',
        f'{course_slug}:lesson_{lesson_number}'
    )


async def show_course_progress_inline(user_id: int, course_slug: str) -> str:
    """
    Возвращает компактный текст прогресса для вставки в любое сообщение
    
    Example:
        text = "Урок 5: Промты для анализа"
        text += await show_course_progress_inline(user_id, 'prompt_engineering')
    """
    
    progress = db.get_user_progress(user_id, course_slug)
    
    completed = progress['completed']
    total = progress['total']
    percentage = progress['percentage']
    
    return f"\n\n📊 Прогресс: {completed}/{total} ({percentage}%)"


# Вспомогательные функции для интеграции

def get_course_slug_from_context(course_name: str) -> str:
    """Получить slug курса по его названию"""
    course_mapping = {
        'prompt_engineering': 'prompt_engineering',
        'vibe_coding': 'vibe_coding',
        'Промт-инженерия': 'prompt_engineering',
        'Vibe Coding': 'vibe_coding'
    }
    return course_mapping.get(course_name, 'prompt_engineering')