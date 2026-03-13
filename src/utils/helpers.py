import re

# Названия модулей
MODULE_NAMES = {
    # Курс 1: Промт-инженерия
    1: "Основы текстового промта",
    2: "Промтинг для таблиц, аналитики и проектных задач",
    3: "Как писать визуальные промпты",
    4: "Промтинг для видео и аудио",
    5: "Продвинутые техники промтинга",
    # Курс 3: Веб-приложения на ИИ
    6: "Основы веб-разработки с ИИ",
    7: "Фронтенд и интеграция ИИ",
    8: "Бэкенд и ИИ-сервисы",
    9: "Продвинутые техники",
    10: "Финальный проект",
}

def add_emojis_to_text(text: str) -> str:
    """Добавление эмоджи для визуализации"""
    emoji_map = {
        r'\b(важно|внимание|ограничение)\b': '⚠️',
        r'\b(пример|например)\b': '💡',
        r'\b(задача|задание)\b': '📝',
        r'\b(цель|результат)\b': '🎯',
        r'\b(роль|контекст)\b': '🎭',
        r'\b(формат|структура)\b': '📋',
        r'\b(тон|стиль)\b': '🎨',
        r'\b(промпт|запрос)\b': '✍️',
        r'\b(ии|нейросеть|chatgpt|claude)\b': '🤖',
        r'\b(данные|таблица|excel)\b': '📊',
        r'\b(текст|документ|письмо)\b': '📄',
        r'\b(изображение|картинка|фото)\b': '🖼️',
        r'\b(видео|ролик)\b': '🎬',
        r'\bРаздел\b': '📌',
    }
    
    for pattern, emoji in emoji_map.items():
        text = re.sub(pattern, f'{emoji} \\g<0>', text, flags=re.IGNORECASE)
    
    return text

def sanitize_markdown(text: str) -> str:
    """Очистка и адаптация текста"""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'-{3,}', '', text)
    text = re.sub(r'={3,}', '', text)
    text = text.replace('**', '*')
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = add_emojis_to_text(text)
    return text.strip()

def split_lesson_into_sections(content: str) -> list:
    """Разбивка урока на разделы"""
    content = sanitize_markdown(content)
    sections = re.split(r'РАЗДЕЛ \d+:', content)
    sections = [s.strip() for s in sections if s.strip() and len(s.strip()) > 50]
    
    if len(sections) <= 1:
        sections = []
        while content:
            sections.append(content[:1500])
            content = content[1500:]
    
    return sections