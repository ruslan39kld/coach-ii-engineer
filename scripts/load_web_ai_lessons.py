"""
Загрузка уроков курса "Веб-приложения на ИИ" (course_id=3) в БД.

Если в папке data/web_ai_lessons/ есть файлы вида lesson_<N>.txt —
они используются как контент урока. Если файла нет — используется
встроенный placeholder, который можно заменить позже.

Структура:
    Модуль 1  (4 урока, lesson_no 1–4)   — Введение и основы
    Модуль 2  (5 уроков, lesson_no 5–9)  — Монологовые приложения
    Модуль 3  (4 урока, lesson_no 10–13) — Диалоговые приложения
    Модуль 4  (3 урока, lesson_no 14–16) — От прототипа к продакшену
    Модуль 5  (2 урока, lesson_no 17–18) — Продвинутые техники
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
    # Модуль 1: Введение и основы
    (1, 1):  "Введение в Google AI Studio — революция в разработке",
    (1, 2):  "От идеи до приложения — процесс генерации и редактирования",
    (1, 3):  "Анатомия AI веб-приложения — структура файлов и geminiService",
    (1, 4):  "Локальная разработка и публикация приложений",

    # Модуль 2: Монологовые приложения
    (2, 5):  "Первое AI-приложение — анализатор текста",
    (2, 6):  "Приложение с файлами — AI-секретарь совещаний",
    (2, 7):  "Форматированный вывод — генератор контента",
    (2, 8):  "Работа с данными — JSON хранилище",
    (2, 9):  "Стилизация и адаптивный дизайн",

    # Модуль 3: Диалоговые приложения
    (3, 10): "Чат-интерфейс с историей и streaming",
    (3, 11): "AI-консультант по продаже абонементов",
    (3, 12): "Продавщик с ветвлением — система сборки пиццы",
    (3, 13): "Многоагентная система — AI-ветеринар",

    # Модуль 4: От прототипа к продакшену
    (4, 14): "Оптимизация и производительность",
    (4, 15): "Обработка ошибок и edge cases",
    (4, 16): "Тестирование и отладка",

    # Модуль 5: Продвинутые техники
    (5, 17): "Интеграции с внешними API",
    (5, 18): "Создание полноценного продукта — итоговый проект",
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
        print(f"  ✅ M{module_no} L{lesson_no:>2}: {title} [{source}]")
        loaded += 1

    conn.commit()
    conn.close()
    print(f"\n🎉 Загружено уроков: {loaded} (course_id={COURSE_ID})")


if __name__ == '__main__':
    main()
