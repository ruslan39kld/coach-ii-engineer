"""
Загрузка уроков курса "Веб-приложения на ИИ" (course_id=3) в БД.

Скрипт предназначен для запуска на Windows-машине, где расположены файлы уроков.
Ищет файлы urok*.txt рекурсивно в LESSONS_DIR, извлекает module_no из имени папки.

Структура папок:
    МОДУЛЬ 1 ВВЕДЕНИЕ И ОСНОВЫ\УРОК 1 ...\urok1_*.txt
    МОДУЛЬ 2 ...\УРОК 5 ...\urok5_*.txt
    ...
"""

import os
import sys
import sqlite3
import re
from pathlib import Path

DB_PATH = "data/bot.db"
LESSONS_DIR = r"C:\Users\BeltiugovRV\Desktop\ПРОЕКТЫ\1. AI Инженер\БАЗА\Веб-приложения"
COURSE_ID = 3


def extract_lesson_no(filename):
    """Извлекает номер урока из имени файла: urok1_... → 1"""
    match = re.match(r'urok(\d+)_', filename, re.IGNORECASE)
    return int(match.group(1)) if match else None


def extract_module_no(folder_path):
    """Извлекает номер модуля из пути папки: МОДУЛЬ 1 ... → 1"""
    for part in Path(folder_path).parts:
        match = re.search(r'МОДУЛЬ\s+(\d+)', part, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def find_all_lessons(root_dir):
    """Рекурсивно ищет все файлы urok*.txt и возвращает список (lesson_no, module_no, filepath)."""
    lessons = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if re.match(r'urok\d+.*\.txt$', filename, re.IGNORECASE):
                lesson_no = extract_lesson_no(filename)
                module_no = extract_module_no(dirpath)
                if lesson_no is not None and module_no is not None:
                    lessons.append((lesson_no, module_no, os.path.join(dirpath, filename)))
    lessons.sort(key=lambda x: x[0])
    return lessons


def placeholder_content(module_no: int, lesson_no: int, title: str) -> str:
    """Генерирует placeholder-контент урока."""
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


# Маппинг lesson_no → title (используется как fallback если файл не найден)
TITLE_MAPPING = {
    1:  "Введение в Google AI Studio — революция в разработке",
    2:  "От идеи до приложения — процесс генерации и редактирования",
    3:  "Анатомия AI веб-приложения — структура файлов и geminiService",
    4:  "Локальная разработка и публикация приложений",
    5:  "Первое AI-приложение — анализатор текста",
    6:  "Приложение с файлами — AI-секретарь совещаний",
    7:  "Форматированный вывод — генератор контента",
    8:  "Работа с данными — JSON хранилище",
    9:  "Стилизация и адаптивный дизайн",
    10: "Чат-интерфейс с историей и streaming",
    11: "AI-консультант по продаже абонементов",
    12: "Продавщик с ветвлением — система сборки пиццы",
    13: "Многоагентная система — AI-ветеринар",
    14: "Оптимизация и производительность",
    15: "Обработка ошибок и edge cases",
    16: "Тестирование и отладка",
    17: "Интеграции с внешними API",
    18: "Создание полноценного продукта — итоговый проект",
}

MODULE_FOR_LESSON = {
    1: 1, 2: 1, 3: 1, 4: 1,
    5: 2, 6: 2, 7: 2, 8: 2, 9: 2,
    10: 3, 11: 3, 12: 3, 13: 3,
    14: 4, 15: 4, 16: 4,
    17: 5, 18: 5,
}


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


def load_lessons():
    if not os.path.exists(LESSONS_DIR):
        print(f"❌ Папка не найдена: {LESSONS_DIR}")
        return

    lessons = find_all_lessons(LESSONS_DIR)
    if not lessons:
        print(f"⚠️  Файлы urok*.txt не найдены в {LESSONS_DIR}")
        return

    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    ensure_tables(cursor)

    cursor.execute("DELETE FROM lesson_catalog WHERE course_id = ?", (COURSE_ID,))
    print(f"🗑️  Старые уроки курса {COURSE_ID} удалены\n")
    print(f"📚 Найдено файлов: {len(lessons)}\n")

    loaded = 0
    try:
        for lesson_no, module_no, filepath in lessons:
            filename = os.path.basename(filepath)
            title = TITLE_MAPPING.get(lesson_no, filename.replace('.txt', '').replace('_', ' ').strip())

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            cursor.execute("""
                INSERT INTO lesson_catalog (module_no, lesson_no, title, file_path, content, course_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (module_no, lesson_no, title, filepath, content, COURSE_ID))

            print(f"  ✅ M{module_no} L{lesson_no:>2}: {filename}")
            loaded += 1

        conn.commit()
        print(f"\n🎉 Загружено уроков Веб-приложения на ИИ: {loaded} (course_id={COURSE_ID})")

        cursor.execute("""
            SELECT module_no, COUNT(*) FROM lesson_catalog
            WHERE course_id = ? GROUP BY module_no ORDER BY module_no
        """, (COURSE_ID,))
        print("\n📊 Уроков по модулям:")
        for row in cursor.fetchall():
            print(f"   Модуль {row[0]}: {row[1]} уроков")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == '__main__':
    load_lessons()
