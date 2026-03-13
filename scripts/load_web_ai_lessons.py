"""
Загрузка уроков курса "Веб-приложения на ИИ" (course_id=3) в БД.

Если в папке data/web_ai_lessons/ есть файлы вида lesson_<N>.txt —
они используются как контент урока. Если файла нет — используется
встроенный placeholder, который можно заменить позже.

Структура:
    Модуль 6  (4 урока, lesson_no 1–4)   — Основы веб-разработки с ИИ
    Модуль 7  (4 урока, lesson_no 5–8)   — Фронтенд и интеграция ИИ
    Модуль 8  (4 урока, lesson_no 9–12)  — Бэкенд и ИИ-сервисы
    Модуль 9  (3 урока, lesson_no 13–15) — Продвинутые техники
    Модуль 10 (3 урока, lesson_no 16–18) — Финальный проект
"""

import os
import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import config

DB_PATH = Path(config.DB_PATH)
LESSONS_DIR = Path(__file__).parent.parent / 'data' / 'web_ai_lessons'
COURSE_ID = 3


# ---------------------------------------------------------------------------
# Маппинг: (module_no, lesson_no) → title
# ---------------------------------------------------------------------------
LESSONS_MAPPING = {
    # Модуль 6: Основы веб-разработки с ИИ
    (6, 1):  "Введение в веб-разработку с ИИ",
    (6, 2):  "Инструменты и стек технологий",
    (6, 3):  "Первое веб-приложение с ИИ",
    (6, 4):  "Проектирование интерфейсов",

    # Модуль 7: Фронтенд и интеграция ИИ
    (7, 5):  "HTML/CSS с помощью ИИ",
    (7, 6):  "JavaScript и ИИ-ассистенты",
    (7, 7):  "Подключение LLM к фронтенду",
    (7, 8):  "Чат-интерфейс для ИИ",

    # Модуль 8: Бэкенд и ИИ-сервисы
    (8, 9):  "Серверная часть на Python/FastAPI",
    (8, 10): "RAG для веб-приложений",
    (8, 11): "Аутентификация и безопасность",
    (8, 12): "База данных и хранилище",

    # Модуль 9: Продвинутые техники
    (9, 13): "Деплой веб-приложения",
    (9, 14): "Оптимизация и производительность",
    (9, 15): "Мультимодальный ИИ в вебе",

    # Модуль 10: Финальный проект
    (10, 16): "Монетизация и продвижение",
    (10, 17): "Финальный проект: планирование",
    (10, 18): "Финальный проект: реализация",
}


def placeholder_content(module_no: int, lesson_no: int, title: str) -> str:
    """Генерирует placeholder-контент урока в формате, пригодном для разбивки на разделы."""
    return f"""РАЗДЕЛ 1: Введение
Урок {lesson_no}. {title}

Добро пожаловать в урок {lesson_no} модуля {module_no} курса «Веб-приложения на ИИ».
В этом уроке вы освоите ключевые концепции темы: {title}.

Современные инструменты ИИ кардинально меняют подход к веб-разработке.
Вы научитесь применять их для создания реальных продуктов.

РАЗДЕЛ 2: Основная теория
Ключевые понятия урока

В этом разделе рассматриваются теоретические основы темы «{title}».

Основные концепции:
• Понятие и назначение
• Принципы работы
• Практическое применение
• Типичные ошибки и как их избежать

Изучите материал внимательно — на основе этого раздела будет тест.

РАЗДЕЛ 3: Практика
Практические задания

Закрепите знания из урока «{title}» на практике.

Задание 1: Изучите инструменты, связанные с темой урока.
Задание 2: Создайте простой прототип, используя изученные концепции.
Задание 3: Протестируйте результат и зафиксируйте наблюдения.

После выполнения заданий пройдите тест для закрепления материала.
"""


def get_lesson_content(module_no: int, lesson_no: int, title: str) -> str:
    """Возвращает контент урока: из файла или placeholder."""
    file_path = LESSONS_DIR / f'lesson_{lesson_no}.txt'
    if file_path.exists():
        return file_path.read_text(encoding='utf-8')
    return placeholder_content(module_no, lesson_no, title)


def ensure_tables(cursor: sqlite3.Cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lesson_catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_no INTEGER,
            lesson_no INTEGER,
            title TEXT,
            file_path TEXT,
            content TEXT,
            test_data TEXT,
            course_id INTEGER DEFAULT 1
        )
    """)
    try:
        cursor.execute("ALTER TABLE lesson_catalog ADD COLUMN course_id INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    ensure_tables(cursor)

    # Удаляем старые уроки курса 3
    cursor.execute("DELETE FROM lesson_catalog WHERE course_id = ?", (COURSE_ID,))
    print(f"🗑️  Старые уроки курса {COURSE_ID} удалены")

    loaded = 0
    for (module_no, lesson_no), title in sorted(LESSONS_MAPPING.items()):
        content = get_lesson_content(module_no, lesson_no, title)
        file_path = str(LESSONS_DIR / f'lesson_{lesson_no}.txt')

        cursor.execute("""
            INSERT INTO lesson_catalog (module_no, lesson_no, title, file_path, content, course_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (module_no, lesson_no, title, file_path, content, COURSE_ID))

        source = "файл" if (LESSONS_DIR / f'lesson_{lesson_no}.txt').exists() else "placeholder"
        print(f"  ✅ M{module_no} L{lesson_no}: {title} [{source}]")
        loaded += 1

    conn.commit()
    conn.close()
    print(f"\n🎉 Загружено уроков: {loaded} (course_id={COURSE_ID})")


if __name__ == '__main__':
    main()
