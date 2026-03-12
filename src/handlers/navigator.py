from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

async def show_navigator(callback: CallbackQuery):
    """Навигатор"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Текстовые ИИ", callback_data="nav_text")],
        [InlineKeyboardButton(text="🎨 Генерация изображений", callback_data="nav_image")],
        [InlineKeyboardButton(text="🎬 Видео и аудио", callback_data="nav_video")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(
        "🧭 *НАВИГАТОР ПО НЕЙРОСЕТЯМ*\n\nВыберите категорию:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

# ============================================================================
# ТЕКСТОВЫЕ ИИ
# ============================================================================

async def nav_text(callback: CallbackQuery):
    """Текстовые ИИ - меню разделов"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Список нейросетей", callback_data="nav_text_list")],
        [InlineKeyboardButton(text="🔬 Сравнение", callback_data="nav_text_compare")],
        [InlineKeyboardButton(text="🎯 Тактики", callback_data="nav_text_tactics")],
        [InlineKeyboardButton(text="💡 Лайфхаки", callback_data="nav_text_lifehacks")],
        [InlineKeyboardButton(text="⚠️ Подводные камни", callback_data="nav_text_pitfalls")],
        [InlineKeyboardButton(text="📋 Шпаргалка", callback_data="nav_text_cheatsheet")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="mode_navigator")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(
        "*✍️ ТЕКСТОВЫЕ ИИ*\n\nВыберите раздел:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

async def nav_text_list(callback: CallbackQuery, db):
    """Список текстовых нейросетей"""
    tools = db.get_ai_tools_by_category("Текстовые ИИ")
    
    if not tools:
        await callback.message.edit_text("Данные загружаются...", parse_mode="Markdown")
        await callback.answer()
        return
    
    response = "*✍️ ТЕКСТОВЫЕ ИИ*\n\n"
    
    foreign = [t for t in tools if t['region'] == 'Зарубежная']
    russian = [t for t in tools if t['region'] == 'Российская']
    
    if russian:
        response += "*🇷🇺 РОССИЙСКИЕ:*\n\n"
        for tool in russian:
            response += f"*{tool['name']}*\n{tool['description']}\n"
            if tool['access_info']:
                response += f"📍 {tool['access_info']}\n"
            response += "\n"
    
    if foreign:
        response += "*🌍 ЗАРУБЕЖНЫЕ:*\n\n"
        for tool in foreign:
            response += f"*{tool['name']}*\n{tool['description']}\n"
            if tool['access_info']:
                response += f"📍 {tool['access_info']}\n"
            response += "\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="nav_text")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(response, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

async def nav_text_compare(callback: CallbackQuery):
    """Сравнение текстовых ИИ"""
    text = """*🔬 СРАВНЕНИЕ ТЕКСТОВЫХ ИИ*

*Реальный эксперимент: одна задача – семь решений*

📝 Задача: Составь вежливый отказ организации в проведении массового мероприятия из-за ремонтных работ

*ChatGPT:*
Уважаемые коллеги! С сожалением информируем вас, что в связи с проведением плановых ремонтных работ... [3 абзаца]

*YandexGPT:*
Уважаемые организаторы! К сожалению, не можем согласовать проведение мероприятия в указанные сроки. Площадка закрыта на ремонт до 15 марта.

*Claude:*
Благодарим за обращение и интерес к проведению мероприятия на нашей площадке. К сожалению, в запрашиваемый период... [С альтернативами]

*Kimi:*
В соответствии с планом ремонтных работ, утверждённым приказом №123 от 01.02.2024, площадка будет закрыта.

*Qwen:*
Здравствуйте! Спасибо за ваше предложение. К сожалению, площадка будет на ремонте. Давайте обсудим другие варианты.

*GigaChat:*
В ответ на ваше обращение №123 от 10.11.2024 сообщаем следующее:
1) Площадка недоступна по причине ремонта;
2) Период работ: 01.02-15.03;
3) Альтернативные даты: после 15.03

*DeepSeek:*
Рассмотрев ваше предложение о проведении мероприятия и сопоставив с графиком работ (Приложение 1), вынуждены отказать по объективным причинам..."""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="nav_text")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

async def nav_text_tactics(callback: CallbackQuery):
    """Тактики работы с текстовыми ИИ"""
    text = """*🎯 ТАКТИКА "БЕСПЛАТНЫЙ СПЕЦНАЗ"*

*Схема работы для экономных:*

1️⃣ *Основной инструмент:* GigaChat (бесплатно, по-русски)

2️⃣ *Для формул и расчётов:* DeepSeek (бесплатный GPT-4!)

3️⃣ *Для больших документов:* Kimi (200 страниц осилит)

4️⃣ *Для проверки фактов:* Perplexity (с источниками и разными ИИ моделями)

5️⃣ *Для важных документов:* LMArena (два мнения сразу)

6️⃣ *Запасной:* Qwen (когда остальные перегружены)

*Комбо-приём "Бесплатная сборная":*

Пример задачи: нужен отчёт по исполнению бюджета с анализом и рекомендациями

- DeepSeek – создаёт формулы для расчётов
- Kimi – анализирует прошлогодний отчёт (50 страниц)
- YandexGPT/GigaChat – пишет текст по российским стандартам
- Perplexity – проверяет актуальные нормативы
- LMArena – даёт два варианта заключения

✅ Результат: профессиональный отчёт без копейки затрат!"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="nav_text")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

async def nav_text_lifehacks(callback: CallbackQuery):
    """Лайфхаки для текстовых ИИ"""
    text = """*💡 ЛАЙФХАКИ ОТ БЫВАЛЫХ*

*Лайфхак #1: "Ротация"*
- Перегружен ChatGPT? → DeepSeek
- Лагает DeepSeek? → Qwen
- Всё висит? → YandexGPT/GigaChat спасёт

*Лайфхак #2: "Двойная проверка"*
- Таблицы и формулы → DeepSeek
- Длинные документы → Kimi
- Российская специфика → YandexGPT/GigaChat
- Быстрый драфт → Qwen

*Лайфхак #3: "Специализация"*
Важный документ? Прогоните через LMArena – получите два мнения бесплатно!

*Лайфхак #4: "Франкенштейн"*
Соберите идеальный документ из кусочков от разных ИИ — каждый даст своё лучшее!"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="nav_text")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

async def nav_text_pitfalls(callback: CallbackQuery):
    """Подводные камни текстовых ИИ"""
    text = """*⚠️ ПОДВОДНЫЕ КАМНИ БЕСПЛАТНЫХ СЕРВИСОВ*

*Проблема #1:* Интерфейс на английском/китайском
✅ Решение: браузер с автопереводом или пишите промпты на русском – пойдут!

*Проблема #2:* Лимиты и очереди
✅ Решение: имейте 3-4 альтернативы, не зависьте от одного сервиса

*Проблема #3:* Не знают российских реалий
✅ Решение: давайте больше контекста, приводите примеры

*Проблема #4:* Регистрация через зарубежные сервисы
✅ Решение: используйте YandexGPT и GigaChat – наши, родные!"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="nav_text")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

async def nav_text_cheatsheet(callback: CallbackQuery):
    """Шпаргалка по текстовым ИИ"""
    text = """*📋 ШПАРГАЛКА: "КАКОЙ ИИ ДЛЯ ЧЕГО"*

*Для текстов и писем:*
💰 Платно: ChatGPT-4, Claude
🆓 Бесплатно: YandexGPT, Qwen

*Для формул и данных:*
💰 Платно: ChatGPT-4 с плагинами
🆓 Бесплатно: DeepSeek (лучший выбор!)

*Для больших документов:*
💰 Платно: Claude Pro
🆓 Бесплатно: Kimi (до 200 страниц!)

*Для проверки фактов:*
⭐ Всегда: Perplexity (частично бесплатно)

*Для важных документов:*
⭐ Всегда: LMArena (сравните варианты!)

*Для российской специфики:*
💰 Платно: GigaChat
🆓 Бесплатно: YandexGPT"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="nav_text")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

# ============================================================================
# ИЗОБРАЖЕНИЯ
# ============================================================================

async def nav_image(callback: CallbackQuery):
    """Генерация изображений - меню разделов"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Список нейросетей", callback_data="nav_image_list")],
        [InlineKeyboardButton(text="🔬 Сравнение", callback_data="nav_image_compare")],
        [InlineKeyboardButton(text="🎯 Тактики", callback_data="nav_image_tactics")],
        [InlineKeyboardButton(text="💡 Лайфхаки", callback_data="nav_image_lifehacks")],
        [InlineKeyboardButton(text="⚠️ Подводные камни", callback_data="nav_image_pitfalls")],
        [InlineKeyboardButton(text="📋 Шпаргалка", callback_data="nav_image_cheatsheet")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="mode_navigator")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(
        "*🎨 ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ*\n\nВыберите раздел:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

async def nav_image_list(callback: CallbackQuery, db):
    """Список нейросетей для изображений"""
    tools = db.get_ai_tools_by_category("Генерация изображений")
    
    if not tools:
        await callback.message.edit_text("Данные загружаются...", parse_mode="Markdown")
        await callback.answer()
        return
    
    response = "*🎨 ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ*\n\n"
    
    foreign = [t for t in tools if t['region'] == 'Зарубежная']
    russian = [t for t in tools if t['region'] == 'Российская']
    
    if russian:
        response += "*🇷🇺 РОССИЙСКИЕ:*\n\n"
        for tool in russian:
            response += f"*{tool['name']}*\n{tool['description']}\n"
            if tool['access_info']:
                response += f"📍 {tool['access_info']}\n"
            response += "\n"
    
    if foreign:
        response += "*🌍 ЗАРУБЕЖНЫЕ:*\n\n"
        for tool in foreign:
            response += f"*{tool['name']}*\n{tool['description']}\n"
            if tool['access_info']:
                response += f"📍 {tool['access_info']}\n"
            response += "\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="nav_image")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(response, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

async def nav_image_compare(callback: CallbackQuery):
    """Сравнение ИИ для изображений"""
    text = """*🔬 РЕАЛЬНЫЙ ЭКСПЕРИМЕНТ*

Протестируем промпт: _Сотрудники администрации обсуждают новый проект благоустройства за круглым столом_

*Shedevrum:*
- Реалистичных российских чиновников в деловой одежде
- Узнаваемый кабинет администрации
- Естественные позы и выражения лиц
- Документы и папки на столе

*GigaChat Vision:*
- Более схематичное, "презентационное" изображение
- Четкую деловую композицию
- Менее детализированные, но "правильные" лица
- Подходящее для слайдов качество

*Кандинский:*
- Художественную интерпретацию встречи
- Необычные ракурсы или стилизацию
- Творческий подход к освещению
- Менее предсказуемый, но интересный результат

*Flux (через LMArena):*
- Профессиональное качество детализации
- Идеальное освещение и композицию
- Возможно, слишком "западный" вид людей
- Техническое совершенство изображения"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="nav_image")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

async def nav_image_tactics(callback: CallbackQuery):
    """Тактики для генерации изображений"""
    text = """*🎯 ТАКТИКА "БЕСПЛАТНЫЙ АРСЕНАЛ"*

*Схема работы для экономных:*

1️⃣ *Основной инструмент:* Shedevrum (реализм, российская специфика)

2️⃣ *Для инфографики:* GigaChat Vision (схемы, диаграммы)

3️⃣ *Для творческих задач:* Кандинский (креатив, эксперименты)

4️⃣ *Для высокого качества:* LMArena → Flux

5️⃣ *Для текста на картинках:* LMArena → Ideogram

6️⃣ *Запасной универсал:* Qwen VL

*Комбо-прием "Бесплатная студия":*

Пример: Серия материалов для презентации о развитии туризма

- Shedevrum – создает фото туристов на местных достопримечательностях
- GigaChat Vision – делает инфографику по статистике турпотока
- Кандинский – рисует креативную обложку презентации
- LMArena/Flux – генерирует качественные виды природы региона
- LMArena/Ideogram – создает логотип туристского бренда

✅ Результат: Профессиональная презентация без копейки затрат!"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="nav_image")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

async def nav_image_lifehacks(callback: CallbackQuery):
    """Лайфхаки для изображений"""
    text = """*💡 ЛАЙФХАКИ ОТ БЫВАЛЫХ*

*Лайфхак #1: "Ротация сервисов"*
- Портреты людей → Shedevrum
- Инфографика → GigaChat Vision
- Креатив → Кандинский
- Высокое качество → LMArena/Flux
- Текст на картинках → LMArena/Ideogram

*Лайфхак #2: "Двойная проверка"*
Важное изображение? Сгенерируйте в двух сервисах и выберите лучшее!

*Лайфхак #3: "Специализация"*
Не знаете, какая модель лучше для вашей задачи? Протестируйте в LMArena!

*Лайфхак #4: "Конвейер качества"*
Shedevrum для черновика → GigaChat Vision для схем → Кандинский для креатива"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="nav_image")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

async def nav_image_pitfalls(callback: CallbackQuery):
    """Подводные камни генерации изображений"""
    text = """*⚠️ ПОДВОДНЫЕ КАМНИ БЕСПЛАТНЫХ СЕРВИСОВ*

*Проблема #1:* Дневные лимиты генераций
✅ Решение: имейте 3-4 альтернативы, ротируйте сервисы

*Проблема #2:* Интерфейс на английском (LMArena, Qwen)
✅ Решение: браузер с автопереводом или пишите промпты на русском – поймут!

*Проблема #3:* Не знают российских реалий (зарубежные ИИ)
✅ Решение: давайте больше контекста: "российская администрация", "чиновник в России"

*Проблема #4:* Нестабильная работа
✅ Решение: сохраняйте удачные результаты сразу, не полагайтесь на историю

*Проблема #5:* Условный доступ для некоторых сервисов
✅ Решение: сначала исчерпайте российские альтернативы"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="nav_image")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

async def nav_image_cheatsheet(callback: CallbackQuery):
    """Шпаргалка по генерации изображений"""
    text = """*📋 ШПАРГАЛКА: "КАКОЙ ИИ ДЛЯ ЧЕГО"*

*Для фотореализма:*
🆓 Бесплатно: Shedevrum, Flux (LMArena)
💰 Платно: Midjourney

*Для инфографики и схем:*
🆓 Бесплатно: GigaChat Vision, Ideogram (LMArena)
💰 Платно: специализированные дизайн-инструменты

*Для творческих задач:*
🆓 Бесплатно: Кандинский, Flux (LMArena)
💰 Платно: Midjourney, Adobe Firefly

*Для российской специфики:*
⭐ Всегда: Shedevrum, GigaChat Vision

*Для быстрого результата:*
⭐ Всегда: Shedevrum, Qwen VL

*Для максимального качества:*
🆓 Бесплатно: Flux через LMArena
💰 Платно: Midjourney"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="nav_image")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

# ============================================================================
# ВИДЕО
# ============================================================================

async def nav_video(callback: CallbackQuery):
    """Видео и аудио - меню разделов"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Список нейросетей", callback_data="nav_video_list")],
        [InlineKeyboardButton(text="🔬 Сравнение", callback_data="nav_video_compare")],
        [InlineKeyboardButton(text="🎯 Тактики", callback_data="nav_video_tactics")],
        [InlineKeyboardButton(text="💡 Лайфхаки", callback_data="nav_video_lifehacks")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="mode_navigator")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(
        "*🎬 ВИДЕО И АУДИО*\n\nВыберите раздел:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

async def nav_video_list(callback: CallbackQuery, db):
    """Список нейросетей для видео"""
    tools = db.get_ai_tools_by_category("Видео и аудио")
    
    if not tools:
        await callback.message.edit_text("Данные загружаются...", parse_mode="Markdown")
        await callback.answer()
        return
    
    response = "*🎬 ВИДЕО И АУДИО*\n\n"
    
    foreign = [t for t in tools if t['region'] == 'Зарубежная']
    russian = [t for t in tools if t['region'] == 'Российская']
    
    if russian:
        response += "*🇷🇺 РОССИЙСКИЕ:*\n\n"
        for tool in russian:
            response += f"*{tool['name']}*\n{tool['description']}\n"
            if tool['access_info']:
                response += f"📍 {tool['access_info']}\n"
            response += "\n"
    
    if foreign:
        response += "*🌍 ЗАРУБЕЖНЫЕ:*\n\n"
        for tool in foreign:
            response += f"*{tool['name']}*\n{tool['description']}\n"
            if tool['access_info']:
                response += f"📍 {tool['access_info']}\n"
            response += "\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="nav_video")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(response, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

async def nav_video_compare(callback: CallbackQuery):
    """Сравнение видео-ИИ"""
    text = """*🔬 РЕАЛЬНЫЙ ЭКСПЕРИМЕНТ*

Задача: _создай короткое видео: государственный служащий радостно подписывает документ в современном офисе_

*Шедеврум:*
4-секундный ролик: стилизованный мультяшный персонаж в костюме резко двигает ручкой над бумагой, в фоне размытый российский флаг. Яркие цвета, немного карикатурно.

*Кандинский:*
Красиво прорисованные кадры: реалистичный офис, детализированный стол, аккуратные движения, но переходы между кадрами не плавные. Больше похоже на слайд-шоу.

*Kling AI:*
Очень реалистично: живые эмоции на лице, естественные движения, отличная физика движений, 6 секунд качественного видео.

*Runway ML:*
Фотореалистично: настоящий офис, естественные движения, отличная детализация лица и рук. Плавная анимация, профессиональное освещение. 8 секунд качественного видео.

*Pika Labs:*
Средний реализм: понятно, что человек подписывает документ, движения немного роботизированы, но в целом смотрится неплохо. 3 секунды.

✅ Вывод: каждый ИИ – как режиссер со своим видением и стилем!"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="nav_video")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

async def nav_video_tactics(callback: CallbackQuery):
    """Тактики для видео"""
    text = """*🎯 ТАКТИКА "БЕСПЛАТНАЯ КИНОСТУДИЯ"*

*Схема работы для экономных:*

1️⃣ *Основной инструмент:* Шедеврум (бесплатно, по-русски, быстро)

2️⃣ *Для качественной анимации:* Кандинский (российский, стабильный)

3️⃣ *Для экспериментов:* Pika Labs (бесплатные кредиты)

4️⃣ *Для изображений в видео:* Leonardo.ai (ежедневные бесплатные кредиты)

5️⃣ *Резерв:* Fusion Brain (когда нужен контроль)

*Комбо-приём "Бесплатная продакшн-студия":*

Пример: создать промо-ролик для новой госуслуги

- Шедеврум – создает 3-4 коротких сцены (по 4 сек каждая)
- Кандинский – генерирует статичные заставки и логотипы
- Leonardo.ai – создает дополнительные кадры с инфографикой
- Pika Labs – делает переходы между сценами
- Видеоредактор – склеивает всё в единое видео

✅ Результат: профессиональный ролик за 0 рублей!"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="nav_video")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

async def nav_video_lifehacks(callback: CallbackQuery):
    """Лайфхаки для видео"""
    text = """*💡 ЛАЙФХАКИ ОТ БЫВАЛЫХ*

*Лайфхак #1: "Конвейер качества"*
Берите лучшие кадры от каждого ИИ и комбинируйте в одном проекте:
- Шедеврум → быстрый черновик
- Кандинский → доработка ключевых кадров
- Pika Labs → финальная полировка
- Обычный редактор → склейка и звук

*Лайфхак #2: "Удлинитель коротких видео"*
Создайте 4-5 коротких сцен в Шедеврум и склейте в один длинный ролик!

*Лайфхак #3: "Стиль-миксер"*
Создайте идеальное изображение в Кандинском, затем оживите его в Pika Labs.

*Лайфхак #4: "Промпт-переводчик"*
Сначала создайте подробное описание на русском, потом переведите на английский для зарубежных сервисов.

*Лайфхак #5: "Изображение в движение"*
Берите лучшие кадры от каждого ИИ и комбинируйте в одном проекте."""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="nav_video")]
    ])
    
    # ИЗМЕНЕНО: используем edit_text
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()