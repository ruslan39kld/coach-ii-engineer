from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext

router = Router()

# Словарь для хранения message_id последнего меню каждого пользователя
user_menu_messages = {}

async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎓 Обучение", callback_data="show_course_selection"),
            InlineKeyboardButton(text="🔧 Тренажер", callback_data="mode_trainer")
        ],
        [
            InlineKeyboardButton(text="🧭 Навигатор", callback_data="mode_navigator"),
            InlineKeyboardButton(text="💬 Консультант", callback_data="mode_consultant")
        ],
        [InlineKeyboardButton(text="❓ Что ты можешь?", callback_data="about")]
    ])
    
    sent_message = await message.answer(
        "👋 Добро пожаловать в интеллектуальную платформу AI Инженер!\n\n"
        "Цифровая трансформация и автоматизация задач с помощью ИИ.\n"
        "Освойте технологии искусственного интеллекта для повышения эффективности работы.\n"
        "Экономьте до 70% времени на рутинных процессах.\n\n"
        "<b>Выберите режим работы:</b>\n\n"
        "🎓 <b>Обучение</b> — 2 курса: Промт-инженерия и Vibe Coding\n"
        "🔧 <b>Тренажер</b> — проверка промптов по ПЛК-ФОТ\n"
        "🧭 <b>Навигатор</b> — справочник по нейросетям\n"
        "💬 <b>Консультант</b> — ответы на вопросы по курсу",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    # Сохраняем message_id для этого пользователя
    user_menu_messages[message.from_user.id] = sent_message.message_id

@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎓 Обучение", callback_data="show_course_selection"),
            InlineKeyboardButton(text="🔧 Тренажер", callback_data="mode_trainer")
        ],
        [
            InlineKeyboardButton(text="🧭 Навигатор", callback_data="mode_navigator"),
            InlineKeyboardButton(text="💬 Консультант", callback_data="mode_consultant")
        ],
        [InlineKeyboardButton(text="❓ Что ты можешь?", callback_data="about")]
    ])
    
    # ИЗМЕНЕНО: используем edit_message вместо answer
    await callback.message.edit_text(
        "👋 Добро пожаловать в интеллектуальную платформу AI Инженер!\n\n"
        "Цифровая трансформация и автоматизация задач с помощью ИИ.\n"
        "Освойте технологии искусственного интеллекта для повышения эффективности работы.\n"
        "Экономьте до 70% времени на рутинных процессах.\n\n"
        "<b>Выберите режим работы:</b>\n\n"
        "🎓 <b>Обучение</b> — 2 курса: Промт-инженерия и Vibe Coding\n"
        "🔧 <b>Тренажер</b> — проверка промптов по ПЛК-ФОТ\n"
        "🧭 <b>Навигатор</b> — справочник по нейросетям\n"
        "💬 <b>Консультант</b> — ответы на вопросы по курсу",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    # Обновляем message_id
    user_menu_messages[callback.from_user.id] = callback.message.message_id
    await callback.answer()

@router.callback_query(F.data == "show_course_selection")
async def show_course_selection(callback: CallbackQuery, state: FSMContext):
    """Выбор курса"""
    from services.database import Database
    import config
    
    user_id = callback.from_user.id
    db = Database(config.DB_PATH)
    
    # Проверяем прогресс по course_id=1 и course_id=2
    progress = db.get_user_course_progress(user_id, course_id=1)
    prompt_completed = (progress['completed_lessons'] >= progress['total_lessons'] > 0)
    progress_vibe = db.get_user_course_progress(user_id, course_id=2)
    vibe_completed = (progress_vibe['completed_lessons'] >= progress_vibe['total_lessons'] > 0)
    vibe_module1_completed = db.get_vibe_module1_completed(user_id)
    # Веб-приложения доступны если пройдена Промт-инженерия И Модуль 1 Vibe Coding
    web_unlocked = prompt_completed and vibe_module1_completed

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Промт-инженерия (23 урока)", callback_data="select_course_1")],
        [InlineKeyboardButton(
            text="💻 Vibe Coding (21 урок)" + (" ✅" if prompt_completed else " 🔒"),
            callback_data="select_course_2"
        )],
        [InlineKeyboardButton(
            text="🌐 Веб-приложения на ИИ (18 уроков)" + (" ✅" if web_unlocked else " 🔒"),
            callback_data="select_course_3"
        )],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])

    await state.update_data(
        prompt_completed=prompt_completed,
        vibe_completed=vibe_completed,
        vibe_module1_completed=vibe_module1_completed,
        web_unlocked=web_unlocked,
    )
    
    # ИЗМЕНЕНО: используем edit_text вместо answer
    await callback.message.edit_text(
        "📚 <b>Выбор курса обучения</b>\n\n"
        "Выберите курс для изучения:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    # Обновляем message_id
    user_menu_messages[callback.from_user.id] = callback.message.message_id
    await callback.answer()

@router.callback_query(F.data.startswith("select_course_"))
async def select_course(callback: CallbackQuery, state: FSMContext):
    """Выбор курса"""
    course_id = int(callback.data.split("_")[2])
    
    # Сохраняем course_id
    await state.update_data(selected_course_id=course_id)
    
    # Получаем статус
    data = await state.get_data()
    prompt_completed = data.get("prompt_completed", False)
    
    # Если Vibe Coding И не завершен Промт → показать меню блокировки
    if course_id == 2 and not prompt_completed:
        from handlers.learning import show_vibe_locked_menu
        await show_vibe_locked_menu(callback, state)
        return

    # Если Веб-приложения на ИИ И не выполнены оба условия доступа → показать меню блокировки
    # Условия: пройдена Промт-инженерия (23 урока) И пройден Модуль 1 Vibe Coding (4 урока)
    web_unlocked = data.get("web_unlocked", False)
    if course_id == 3 and not web_unlocked:
        from handlers.learning import show_web_locked_menu
        await show_web_locked_menu(callback, state)
        return
    
    # Иначе запускаем обучение
    from handlers.learning import start_learning_with_course
    from services.database import Database
    import config
    
    db = Database(config.DB_PATH)
    await start_learning_with_course(callback, db, callback.from_user.id, course_id, state)

@router.callback_query(F.data == "about")
async def show_about(callback: CallbackQuery):
    """Что ты можешь? - ОБНОВЛЕННЫЙ ТЕКСТ"""
    about_text = (
        "🤖 <b>ВОЗМОЖНОСТИ ПЛАТФОРМЫ AI ИНЖЕНЕР</b>\n"
        "Профессиональное обучение работе с искусственным интеллектом\n"
        "━━━━━━━━━━━━━━━━\n\n"
        
        "📚 <b>РЕЖИМ «ОБУЧЕНИЕ»</b>\n"
        "• 2 курса: Промт-инженерия (23 урока) и Vibe Coding (21 урок)\n"
        "• 4 модуля с практическими кейсами\n"
        "• 132 теста по урокам + 60 итоговых тестов\n"
        "• Система сохранения прогресса\n"
        "• Применимо в любой профессии\n\n"
        
        "━━━━━━━━━━━━━━━━\n"
        "📝 <b>СИСТЕМА ТЕСТИРОВАНИЯ:</b>\n"
        "✓ 3 теста после каждого урока (132 теста всего)\n"
        "✓ Для прохождения нужно 2 из 3 верных\n"
        "✓ 2 попытки на каждый тест\n"
        "✓ Зеленая 🟢 / красная 🔴 подсветка\n"
        "✓ Объяснения правильных и неправильных ответов\n"
        "✓ При неудаче — повтор урока\n\n"
        
        "🛠 <b>РЕЖИМ «ТРЕНАЖЕР»</b>\n"
        "• Анализ промптов по ПЛК-ФОТ\n"
        "• Оценка от 0 до 10 баллов\n"
        "• Персональные рекомендации\n"
        "• Разбор ошибок с решениями\n\n"
        
        "🧭 <b>РЕЖИМ «НАВИГАТОР»</b>\n"
        "• База из 30+ нейросетей\n"
        "• Сравнение российских и зарубежных ИИ\n"
        "• Тактики, лайфхаки, шпаргалки\n"
        "• Инструкции по доступу\n\n"
        
        "💬 <b>РЕЖИМ «КОНСУЛЬТАНТ»</b>\n"
        "• Ответы на вопросы 24/7\n"
        "• RAG-поиск по базе знаний\n"
        "• Готовые промпты для задач\n"
        "• Помощь в решении кейсов\n\n"
        
        "━━━━━━━━━━━━━━━━\n"
        "⚙️ <b>АДМИН-ПАНЕЛЬ</b>\n"
        "• Общая статистика платформы\n"
        "• Детальная статистика по курсам\n"
        "• Выгрузка отчетов в Excel\n"
        "• ТОП-10 активных пользователей\n"
        "• Список всех пользователей\n"
        "• Мониторинг прогресса в реальном времени\n"
        "• Контроль завершения уроков\n\n"
        
        "━━━━━━━━━━━━━━━━\n"
        "✨ <b>ПРЕИМУЩЕСТВА:</b>\n"
        "✓ Универсальность для любых задач\n"
        "✓ Экономия времени до 70%\n"
        "✓ Рост продуктивности в 3 раза\n"
        "✓ Гарантия усвоения материала\n"
        "✓ Полный контроль обучения\n"
        "✓ Аналитика и отчетность\n\n"
        
        "Версия 2.0 | 2025"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text вместо answer
    await callback.message.edit_text(about_text, reply_markup=keyboard, parse_mode="HTML")
    
    # Обновляем message_id
    user_menu_messages[callback.from_user.id] = callback.message.message_id
    await callback.answer()