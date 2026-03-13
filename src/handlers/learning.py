from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.helpers import sanitize_markdown, split_lesson_into_sections, MODULE_NAMES

# Глобальное хранилище режимов пользователей
user_modes = {}

async def start_learning_with_course(callback: CallbackQuery, db, user_id: int, course_id: int, state: FSMContext):
    """Запуск обучения с указанием курса"""
    import logging
    
    logging.info(f"🎓 Запуск курса {course_id} для пользователя {user_id}")
    
    user_modes[user_id] = "learning"
    
    # Сохраняем course_id
    await state.update_data(selected_course_id=course_id)
    
    # Загружаем прогресс
    m_no, l_no, section = db.get_user_progress(user_id)
    logging.info(f"📖 Прогресс: модуль {m_no}, урок {l_no}, раздел {section}")

    lesson = db.get_lesson(m_no, l_no)

    # Если сохранённый прогресс не соответствует урокам этого курса —
    # начинаем с первого урока курса (актуально для курса 3, где модули 6-10)
    if not lesson:
        first = db.get_first_lesson_for_course(course_id)
        if first:
            m_no, l_no = first
            section = 0
            db.update_user_progress(user_id, m_no, l_no, section)
            lesson = db.get_lesson(m_no, l_no)
            logging.info(f"📖 Начинаем с первого урока курса {course_id}: M{m_no} L{l_no}")

    if not lesson:
        logging.error(f"❌ Урок {m_no}.{l_no} не найден в курсе {course_id}!")
        await callback.answer("Урок не найден")
        return
    
    logging.info(f"✅ Урок загружен: {lesson[0]}")
    
    title, content, _ = lesson
    sections = split_lesson_into_sections(content)
    
    if section >= len(sections):
        section = 0
        db.update_user_progress(user_id, m_no, l_no, section)
    
    section_text = sections[section]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Следующий раздел", callback_data="next_section")],
        [InlineKeyboardButton(text="📋 Список уроков", callback_data="lesson_list")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text для урока
    await callback.message.edit_text(
        f"📖 *Модуль {m_no}, Урок {l_no}*\n"
        f"*{title}*\n\n{section_text}\n\n"
        f"_Раздел {section + 1} из {len(sections)}_",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    await callback.answer()

async def start_learning(callback: CallbackQuery, db, user_id: int, state: FSMContext):
    """Запуск обучения по курсу Промт Инженеринг"""
    await state.clear()
    await start_learning_with_course(callback, db, user_id, 1, state)

async def show_vibe_locked_menu(callback: CallbackQuery, state: FSMContext):
    """Меню для заблокированного Vibe Coding"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Программа курса", callback_data="course_program_vibe")],
        [InlineKeyboardButton(text="📊 Активность", callback_data="course_activity_vibe")],
        [InlineKeyboardButton(text="⚠️ Условия доступа", callback_data="vibe_conditions")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="show_course_selection")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(
        "💻 <b>Vibe Coding (20 уроков)</b>\n\n"
        "⚠️ <b>Курс заблокирован</b>\n\n"
        "Для доступа к курсу необходимо завершить все 23 урока курса \"Промт-инженерия\".\n\n"
        "Вы можете ознакомиться с программой курса и условиями доступа.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

async def next_section(callback: CallbackQuery, db, user_id: int):
    """Следующий раздел урока"""
    m_no, l_no, current_section = db.get_user_progress(user_id)
    lesson = db.get_lesson(m_no, l_no)
    
    if not lesson:
        await callback.answer("Ошибка загрузки урока")
        return
    
    title, content, _ = lesson
    sections = split_lesson_into_sections(content)
    current_section += 1
    
    if current_section >= len(sections):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Пройти тест урока", callback_data="start_test")],
            [InlineKeyboardButton(text="📋 Список уроков", callback_data="lesson_list")]
        ])
        
        # ИЗМЕНЕНО: используем edit_text для завершения урока
        await callback.message.edit_text(
            f"🎉 *Урок {l_no} завершен!*\n\n"
            f"Все разделы урока *{title}* пройдены.\n\n"
            f"❗️ Теперь пройдите тест для закрепления материала.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    db.update_user_progress(user_id, m_no, l_no, current_section)
    
    section_text = sections[current_section]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Следующий раздел", callback_data="next_section")],
        [InlineKeyboardButton(text="📋 Список уроков", callback_data="lesson_list")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text для следующего раздела
    await callback.message.edit_text(
        f"📖 *Модуль {m_no}, Урок {l_no}*\n"
        f"*{title}*\n\n{section_text}\n\n"
        f"_Раздел {current_section + 1} из {len(sections)}_",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

async def show_lesson_list(callback: CallbackQuery, state: FSMContext = None):
    """Меню списка уроков"""
    course_id = 1
    
    if state:
        data = await state.get_data()
        course_id = data.get("selected_course_id", 1)
    
    buttons = [
        [InlineKeyboardButton(text="📖 Программа курса", callback_data="course_program")],
        [InlineKeyboardButton(text="📊 Активность", callback_data="course_activity")],
        [InlineKeyboardButton(text="🔄 Курс с начала", callback_data="restart_course")]
    ]
    
    if course_id == 2:
        buttons.insert(2, [InlineKeyboardButton(text="⚠️ Условия", callback_data="vibe_conditions")])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="show_course_selection")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(
        "*📚 СПИСОК УРОКОВ*\n\nВыберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

async def show_course_program(callback: CallbackQuery, db, state: FSMContext = None):
    """Программа курса ПОЛНАЯ"""
    course_id = 1
    if state:
        data = await state.get_data()
        course_id = data.get("selected_course_id", 1)
    
    all_lessons = db.get_all_lessons()
    
    if course_id == 2:
        lessons = [l for l in all_lessons if l.get('course_id') == 2]
    elif course_id == 3:
        lessons = [l for l in all_lessons if l.get('course_id') == 3]
    else:
        lessons = [l for l in all_lessons if l.get('course_id') in [None, 1]]

    if not lessons:
        await callback.message.edit_text("⚠️ Уроки не найдены в БД", parse_mode="Markdown")
        await callback.answer()
        return

    modules = {}
    for lesson in lessons:
        m_no = lesson['module_no']
        if m_no not in modules:
            modules[m_no] = []
        modules[m_no].append(lesson)

    course_names = {1: "ПРОМТ-ИНЖЕНЕРИЯ", 2: "VIBE CODING", 3: "ВЕБ-ПРИЛОЖЕНИЯ НА ИИ"}
    course_name = course_names.get(course_id, f"КУРС {course_id}")
    text = f"*📖 ПРОГРАММА КУРСА {course_name}*\n\n"
    
    for m_no in sorted(modules.keys()):
        module_name = MODULE_NAMES.get(m_no, f"Модуль {m_no}")
        text += f"*Модуль {m_no}. {module_name}*\n"
        
        for lesson in modules[m_no]:
            l_no = lesson['lesson_no']
            title = lesson['title']
            text += f"  • Урок {l_no}. {title}\n"
        
        text += "\n"
    
    total = len(lessons)
    text += f"*Всего уроков:* {total}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="lesson_list")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

async def show_course_program_vibe(callback: CallbackQuery):
    """Программа Vibe Coding ПОЛНАЯ"""
    text = (
        "*📖 ПРОГРАММА КУРСА VIBE CODING*\n\n"
        
        "*МОДУЛЬ 1: Основы Vibe Coding (4 урока)*\n"
        "• Урок 1: Что такое Vibe Coding и зачем он вам нужен\n"
        "• Урок 2: Возможности Vibe Coding – что можно создавать\n"
        "• Урок 3: Технические основы простыми словами\n"
        "• Урок 4: Методология Vibe Coding на практике\n\n"
        
        "*МОДУЛЬ 2: Создание первого бота (8 уроков)*\n"
        "• Урок 5: Настройка рабочей среды – VS Code\n"
        "• Урок 6: Регистрация бота в Telegram\n"
        "• Урок 7: Hello World – первый работающий бот\n"
        "• Урок 8: Работа с состояниями (FSM)\n"
        "• Урок 9: Первая база данных (SQLite)\n"
        "• Урок 10: Интеграция бота с GigaChat\n"
        "• Урок 11: Настройка промптов для бота\n"
        "• Урок 12: Работа с документами\n\n"
        
        "*МОДУЛЬ 3: Продвинутые возможности (4 урока)*\n"
        "• Урок 13: База знаний и RAG\n"
        "• Урок 14: Гибридный поиск: FAISS + BM25\n"
        "• Урок 15: Логирование, мониторинг и админ-панель\n"
        "• Урок 16: Оптимизация работы бота\n\n"
        "• УРОК 17 Форсаж - UX-оптимизация интерфейса бота\n\n"
        
        "*МОДУЛЬ 4: Production и деплой (4 урока)*\n"
        "• Урок 18: Подготовка к развёртыванию\n"
        "• Урок 19: Деплой бота на сервер\n"
        "• Урок 20: Обновление и поддержка\n"
        "• Урок 21: Финальный проект – ваш бот\n\n"
        
        "*Всего:* 4 модуля, 21 уроков, 60 тестов"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="select_course_2")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

async def show_course_activity_vibe(callback: CallbackQuery):
    """Активность Vibe Coding заблокированного курса"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="select_course_2")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(
        "*📊 АКТИВНОСТЬ*\n\n"
        "⚠️ Курс заблокирован\n\n"
        "Прогресс: 0/21 (0%)\n\n"
        "Завершите курс \"Промт-инженерия\" для доступа.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

async def show_vibe_conditions(callback: CallbackQuery):
    """ПОЛНЫЕ условия доступа"""
    text = (
        "*⚠️ УСЛОВИЯ ДОСТУПА К КУРСУ VIBE CODING*\n\n"
        
        "*✅ ОБЯЗАТЕЛЬНО:*\n"
        "☑ Пройден курс \"Промт-инженерия\" (23 урока)\n"
        "☑ Компьютер (Windows/Mac/Linux)\n"
        "☑ Интернет\n"
        "☑ Желание учиться\n\n"
        
        "*✅ ЖЕЛАТЕЛЬНО:*\n"
        "☑ Telegram аккаунт\n"
        "☑ Аккаунт Сбер ID\n"
        "☑ Готовность экспериментировать\n\n"
        
        "*❌ НЕ НУЖНО:*\n"
        "☒ Знание программирования\n"
        "☒ Дорогое оборудование\n"
        "☒ Большой бюджет\n\n"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="select_course_2")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

async def show_course_activity(callback: CallbackQuery, db, user_id: int, state: FSMContext = None):
    """Активность с правильной фильтрацией"""
    course_id = 1
    if state:
        data = await state.get_data()
        course_id = data.get("selected_course_id", 1)
    
    all_lessons = db.get_all_lessons()
    
    if course_id == 2:
        lessons = [l for l in all_lessons if l.get('course_id') == 2]
    elif course_id == 3:
        lessons = [l for l in all_lessons if l.get('course_id') == 3]
    else:
        lessons = [l for l in all_lessons if l.get('course_id') in [None, 1]]

    completed = db.get_completed_lessons(user_id)
    completed_set = set(completed)
    
    current_m, current_l, _ = db.get_user_progress(user_id)
    
    if not lessons:
        await callback.message.edit_text("⚠️ Уроки не найдены", parse_mode="Markdown")
        await callback.answer()
        return
    
    modules = {}
    for lesson in lessons:
        m_no = lesson['module_no']
        if m_no not in modules:
            modules[m_no] = []
        modules[m_no].append(lesson)
    
    text = "*📊 АКТИВНОСТЬ*\n"
    buttons = []
    
    for m_no in sorted(modules.keys()):
        module_name = MODULE_NAMES.get(m_no, f"Модуль {m_no}")
        
        buttons.append([InlineKeyboardButton(
            text=f"📌 Модуль {m_no}. {module_name}",
            callback_data=f"module_info_{m_no}"
        )])
        
        for lesson in modules[m_no]:
            l_no = lesson['lesson_no']
            title = lesson['title']
            
            if len(title) > 45:
                title = title[:42] + "..."
            
            if (m_no, l_no) in completed_set:
                btn_text = f"✅ Урок {l_no}. {title}"
                buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"goto_{m_no}_{l_no}")])
            elif m_no == current_m and l_no == current_l:
                btn_text = f"▶️ Урок {l_no}. {title}"
                buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"goto_{m_no}_{l_no}")])
            else:
                btn_text = f"   Урок {l_no}. {title}"
                buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"locked_{m_no}_{l_no}")])
    
    total = len(lessons)
    done = len([c for c in completed if any(l['module_no'] == c[0] and l['lesson_no'] == c[1] for l in lessons)])
    percent = int((done / total) * 100) if total > 0 else 0
    
    text += f"\n*Прогресс:* {done}/{total} ({percent}%)"
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="lesson_list")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    # ИЗМЕНЕНО: используем edit_text для списка активности
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

async def restart_course(callback: CallbackQuery, db, user_id: int):
    """Сброс прогресса"""
    import sqlite3
    import logging
    
    try:
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lesson_completions WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        logging.info(f"✅ Очищены уроки для {user_id}")
    except Exception as e:
        logging.error(f"❌ Ошибка: {e}")
    
    db.update_user_progress(user_id, 1, 1, 0)
    
    lesson = db.get_lesson(1, 1)
    
    if not lesson:
        await callback.answer("Ошибка")
        return
    
    title, content, _ = lesson
    sections = split_lesson_into_sections(content)
    section_text = sections[0]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Следующий раздел", callback_data="next_section")],
        [InlineKeyboardButton(text="📋 Список уроков", callback_data="lesson_list")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text для перезапуска курса
    await callback.message.edit_text(
        f"🔄 *Курс начат с начала!*\n\n"
        f"📖 *Модуль 1, Урок 1*\n"
        f"*{title}*\n\n{section_text}\n\n"
        f"_Раздел 1 из {len(sections)}_",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

async def go_to_lesson(callback: CallbackQuery, db, user_id: int):
    """Переход к уроку"""
    parts = callback.data.split("_")
    m_no = int(parts[1])
    l_no = int(parts[2])
    
    lesson = db.get_lesson(m_no, l_no)
    
    if not lesson:
        await callback.answer("Урок не найден")
        return
    
    title, content, _ = lesson
    sections = split_lesson_into_sections(content)
    
    db.update_user_progress(user_id, m_no, l_no, 0)
    
    section_text = sections[0]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Следующий раздел", callback_data="next_section")],
        [InlineKeyboardButton(text="📋 Список уроков", callback_data="lesson_list")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text для перехода к уроку
    await callback.message.edit_text(
        f"📖 *Модуль {m_no}, Урок {l_no}*\n"
        f"*{title}*\n\n{section_text}\n\n"
        f"_Раздел 1 из {len(sections)}_",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

async def module_info(callback: CallbackQuery):
    """Информация о модуле"""
    parts = callback.data.split("_")
    m_no = int(parts[2])
    module_name = MODULE_NAMES.get(m_no, f"Модуль {m_no}")
    await callback.answer(f"Модуль {m_no}: {module_name}", show_alert=False)

async def locked_lesson(callback: CallbackQuery):
    """Недоступный урок"""
    await callback.answer("⚠️ Урок еще не доступен. Завершите текущий урок.", show_alert=True)

async def show_web_locked_menu(callback: CallbackQuery, state: FSMContext):
    """Меню для заблокированного курса Веб-приложения на ИИ"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Программа курса", callback_data="course_program_web")],
        [InlineKeyboardButton(text="📊 Активность", callback_data="course_activity_web")],
        [InlineKeyboardButton(text="⚠️ Условия доступа", callback_data="web_conditions")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="show_course_selection")]
    ])
    await callback.message.edit_text(
        "🌐 <b>Веб-приложения на ИИ (18 уроков)</b>\n\n"
        "⚠️ <b>Курс заблокирован</b>\n\n"
        "Для доступа к курсу необходимо выполнить оба условия:\n"
        "1️⃣ Пройти все 23 урока курса \"Промт-инженерия\"\n"
        "2️⃣ Пройти Модуль 1 курса \"Vibe Coding\" (уроки 1–4)\n\n"
        "Вы можете ознакомиться с программой курса и условиями доступа.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

async def show_course_program_web(callback: CallbackQuery):
    """Программа курса Веб-приложения на ИИ"""
    text = (
        "*📖 ПРОГРАММА КУРСА ВЕБ-ПРИЛОЖЕНИЯ НА ИИ*\n\n"

        "*МОДУЛЬ 1: Введение и основы (4 урока)*\n"
        "• Урок 1. Введение в Google AI Studio — революция в разработке\n"
        "• Урок 2. От идеи до приложения — процесс генерации и редактирования\n"
        "• Урок 3. Анатомия AI веб-приложения — структура файлов и geminiService\n"
        "• Урок 4. Локальная разработка и публикация приложений\n\n"

        "*МОДУЛЬ 2: Монологовые приложения (5 уроков)*\n"
        "• Урок 5. Первое AI-приложение — анализатор текста\n"
        "• Урок 6. Приложение с файлами — AI-секретарь совещаний\n"
        "• Урок 7. Форматированный вывод — генератор контента\n"
        "• Урок 8. Работа с данными — JSON хранилище\n"
        "• Урок 9. Стилизация и адаптивный дизайн\n\n"

        "*МОДУЛЬ 3: Диалоговые приложения (4 урока)*\n"
        "• Урок 10. Чат-интерфейс с историей и streaming\n"
        "• Урок 11. AI-консультант по продаже абонементов\n"
        "• Урок 12. Продавщик с ветвлением — система сборки пиццы\n"
        "• Урок 13. Многоагентная система — AI-ветеринар\n\n"

        "*МОДУЛЬ 4: От прототипа к продакшену (3 урока)*\n"
        "• Урок 14. Оптимизация и производительность\n"
        "• Урок 15. Обработка ошибок и edge cases\n"
        "• Урок 16. Тестирование и отладка\n\n"

        "*МОДУЛЬ 5: Продвинутые техники (2 урока)*\n"
        "• Урок 17. Интеграции с внешними API\n"
        "• Урок 18. Создание полноценного продукта — итоговый проект\n\n"

        "*Всего:* 5 модулей, 18 уроков"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="select_course_3")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

async def show_course_activity_web(callback: CallbackQuery):
    """Активность курса Веб-приложения на ИИ (заблокирован)"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="select_course_3")]
    ])
    await callback.message.edit_text(
        "*📊 АКТИВНОСТЬ*\n\n"
        "⚠️ Курс заблокирован\n\n"
        "Прогресс: 0/18 (0%)\n\n"
        "Для доступа пройдите курс \"Промт-инженерия\" и Модуль 1 \"Vibe Coding\".",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

async def show_web_conditions(callback: CallbackQuery):
    """Условия доступа к курсу Веб-приложения на ИИ"""
    text = (
        "*⚠️ УСЛОВИЯ ДОСТУПА К КУРСУ ВЕБ-ПРИЛОЖЕНИЯ НА ИИ*\n\n"

        "*✅ ОБЯЗАТЕЛЬНО:*\n"
        "☑ Пройден курс \"Промт-инженерия\" (23 урока)\n"
        "☑ Пройден Модуль 1 \"Vibe Coding\" (4 урока)\n"
        "☑ Компьютер (Windows/Mac/Linux)\n"
        "☑ Интернет\n\n"

        "*✅ ЖЕЛАТЕЛЬНО:*\n"
        "☑ Telegram аккаунт\n"
        "☑ Аккаунт Сбер ID\n"
        "☑ Готовность экспериментировать\n\n"

        "*❌ НЕ НУЖНО:*\n"
        "☒ Знание программирования\n"
        "☒ Дорогое оборудование\n"
        "☒ Большой бюджет\n\n"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="select_course_3")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()