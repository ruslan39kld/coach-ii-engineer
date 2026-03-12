"""
Адаптированный обработчик админ-панели для aiogram
Совместимость с существующей системой
"""

from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import sys
import os

# Добавляем путь к базе данных (database на 2 уровня выше)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.db_manager import db
from database.excel_exporter import exporter


# ID администраторов
ADMIN_IDS = [
    1501905373,  # Ваш ID
    307782709    # ID руководителя
]


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id in ADMIN_IDS


async def admin_command(message: types.Message):
    """Главная команда админ-панели /admin"""
    
    user_id = message.from_user.id
    
    # Проверка прав доступа
    if not is_admin(user_id):
        await message.answer(
            "❌ У вас нет доступа к админ-панели.",
            parse_mode='HTML'
        )
        return
    
    # Главное меню админки
    text = """
⚙️ <b>Админ-панель ИИ Инженер</b>

Добро пожаловать в панель управления!

Доступные функции:
• 📊 Общая статистика
• 📥 Выгрузка отчета по прогрессу
• 👥 Список пользователей
• 📈 Статистика по курсам
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Общая статистика", callback_data='admin_general_stats')],
        [InlineKeyboardButton(text="📥 Выгрузить Excel отчет", callback_data='admin_export_excel')],
        [InlineKeyboardButton(text="📈 Статистика по курсам", callback_data='admin_course_stats')],
        [InlineKeyboardButton(text="👥 Топ активных", callback_data='admin_top_users')]
    ])
    
    await message.answer(
        text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )


async def handle_admin_callback(callback: types.CallbackQuery):
    """Обработчик callback-кнопок админки"""
    
    await callback.answer()
    
    user_id = callback.from_user.id
    
    # Проверка прав
    if not is_admin(user_id):
        await callback.message.edit_text(
            "❌ У вас нет доступа к этой функции.",
            parse_mode='HTML'
        )
        return
    
    data = callback.data
    
    if data == 'admin_general_stats':
        await show_general_statistics(callback)
    
    elif data == 'admin_export_excel':
        await export_excel_report(callback)
    
    elif data == 'admin_course_stats':
        await show_course_statistics(callback)
    
    elif data == 'admin_top_users':
        await show_top_users(callback)
    
    elif data == 'admin_back':
        await show_admin_menu(callback)


async def show_admin_menu(callback: types.CallbackQuery):
    """Показать главное меню админки"""
    
    text = """
⚙️ <b>Админ-панель ИИ Инженер</b>

Выберите действие:
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Общая статистика", callback_data='admin_general_stats')],
        [InlineKeyboardButton(text="📥 Выгрузить Excel отчет", callback_data='admin_export_excel')],
        [InlineKeyboardButton(text="📈 Статистика по курсам", callback_data='admin_course_stats')],
        [InlineKeyboardButton(text="👥 Топ активных", callback_data='admin_top_users')]
    ])
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )


async def show_general_statistics(callback: types.CallbackQuery):
    """Показать общую статистику"""
    
    total_users = db.get_total_users()
    courses = db.get_all_courses()
    
    text = f"""
📊 <b>Общая статистика платформы</b>

👥 Всего пользователей: <b>{total_users}</b>

📚 <b>Статистика по курсам:</b>
"""
    
    for course in courses:
        stats = db.get_course_statistics(course['course_slug'])
        text += f"\n<b>{stats['course_name']}</b>\n"
        text += f"• Записано: {stats['enrolled']}\n"
        text += f"• Завершили: {stats['completed']}\n"
        text += f"• В процессе: {stats['in_progress']}\n"
        text += f"• % завершения: {stats['completion_rate']}%\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data='admin_back')]
    ])
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )


async def export_excel_report(callback: types.CallbackQuery):
    """Выгрузить отчет в Excel"""
    
    # Показываем сообщение о процессе
    await callback.message.edit_text(
        "⏳ Генерирую отчет... Пожалуйста, подождите.",
        parse_mode='HTML'
    )
    
    try:
        # Получаем данные
        report_data = db.get_all_users_for_report()
        courses = db.get_all_courses()
        
        # Генерируем Excel
        filepath = exporter.generate_progress_report(report_data, courses)
        
        # Отправляем файл
        file = types.FSInputFile(filepath)
        
        await callback.message.answer_document(
            document=file,
            caption=f"📊 <b>Отчет по прогрессу обучения</b>\n\n"
                   f"👥 Пользователей: {len(report_data)}\n"
                   f"📚 Курсов: {len(courses)}\n"
                   f"📅 Дата: {callback.message.date.strftime('%d.%m.%Y %H:%M')}",
            parse_mode='HTML'
        )
        
        # Удаляем временный файл
        os.remove(filepath)
        
        # Возвращаем меню
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data='admin_back')]
        ])
        
        await callback.message.answer(
            "✅ Отчет успешно сгенерирован!",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
    except Exception as e:
        await callback.message.answer(
            f"❌ Ошибка при генерации отчета:\n<code>{str(e)}</code>",
            parse_mode='HTML'
        )


async def show_course_statistics(callback: types.CallbackQuery):
    """Детальная статистика по курсам"""
    
    courses = db.get_all_courses()
    
    text = "📈 <b>Детальная статистика по курсам</b>\n\n"
    
    for course in courses:
        stats = db.get_course_statistics(course['course_slug'])
        
        text += f"📚 <b>{stats['course_name']}</b>\n"
        text += f"├ Всего записано: <b>{stats['enrolled']}</b>\n"
        text += f"├ Завершили: <b>{stats['completed']}</b> ✅\n"
        text += f"├ В процессе: <b>{stats['in_progress']}</b> ⏸️\n"
        text += f"└ % завершения: <b>{stats['completion_rate']}%</b>\n\n"
        
        # Прогресс-бар
        total_bars = 10
        filled_bars = int(stats['completion_rate'] / 10)
        progress_bar = "█" * filled_bars + "░" * (total_bars - filled_bars)
        text += f"   {progress_bar} {stats['completion_rate']}%\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data='admin_back')]
    ])
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )


async def show_top_users(callback: types.CallbackQuery):
    """Показать топ активных пользователей"""
    
    # Получаем всех пользователей с прогрессом
    users_data = db.get_all_users_for_report()
    
    # Сортируем по суммарному прогрессу
    users_with_progress = []
    
    for user in users_data:
        total_completed = 0
        total_lessons = 0
        
        for course_slug, progress in user['courses'].items():
            total_completed += progress['completed']
            total_lessons += progress['total']
        
        if total_lessons > 0:
            completion_percentage = (total_completed / total_lessons * 100)
        else:
            completion_percentage = 0
        
        users_with_progress.append({
            'user_id': user['user_id'],
            'full_name': user['full_name'],
            'total_completed': total_completed,
            'total_lessons': total_lessons,
            'percentage': completion_percentage
        })
    
    # Сортируем по проценту завершения
    users_with_progress.sort(key=lambda x: x['percentage'], reverse=True)
    
    text = "👥 <b>ТОП-10 активных пользователей</b>\n\n"
    
    for idx, user in enumerate(users_with_progress[:10], start=1):
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}."
        
        text += f"{medal} <b>{user['full_name']}</b>\n"
        text += f"   Завершено: {user['total_completed']}/{user['total_lessons']} ({user['percentage']:.1f}%)\n\n"
    
    if not users_with_progress:
        text += "Пока нет активных пользователей."
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data='admin_back')]
    ])
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )