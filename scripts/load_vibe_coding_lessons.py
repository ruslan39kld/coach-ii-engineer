import sqlite3
import os
import re
from pathlib import Path

DB_PATH = "data/bot.db"
LESSONS_DIR = r"C:\Users\BeltiugovRV\Desktop\ПРОЕКТЫ\1. AI Инженер\БАЗА\Вайб кодинг"


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
    """Рекурсивно ищет все файлы urok*_*.txt и возвращает список (lesson_no, module_no, filepath)."""
    lessons = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if re.match(r'urok\d+_.*\.txt$', filename, re.IGNORECASE):
                lesson_no = extract_lesson_no(filename)
                module_no = extract_module_no(dirpath)
                if lesson_no is not None and module_no is not None:
                    lessons.append((lesson_no, module_no, os.path.join(dirpath, filename)))
    lessons.sort(key=lambda x: x[0])
    return lessons


def load_lessons():
    if not os.path.exists(LESSONS_DIR):
        print(f"❌ Папка не найдена: {LESSONS_DIR}")
        return

    lessons = find_all_lessons(LESSONS_DIR)
    if not lessons:
        print(f"⚠️  Файлы urok*_*.txt не найдены в {LESSONS_DIR}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Удаляем старые уроки Vibe Coding
    cursor.execute("DELETE FROM lesson_catalog WHERE course_id = 2")
    print(f"🗑️  Старые уроки Vibe Coding (course_id=2) удалены\n")
    print(f"📚 Найдено файлов: {len(lessons)}\n")

    loaded = 0
    try:
        for lesson_no, module_no, filepath in lessons:
            filename = os.path.basename(filepath)
            # Заголовок урока — из имени файла без расширения, облагороженный
            title = filename.replace('.txt', '').replace('_', ' ').strip()

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            cursor.execute("""
                INSERT INTO lesson_catalog (module_no, lesson_no, title, file_path, content, course_id)
                VALUES (?, ?, ?, ?, ?, 2)
            """, (module_no, lesson_no, title, filepath, content))

            print(f"  ✅ M{module_no} L{lesson_no:>2}: {filename}")
            loaded += 1

        conn.commit()
        print(f"\n🎉 Загружено уроков Vibe Coding: {loaded} (course_id=2)")

        # Итог по модулям
        cursor.execute("""
            SELECT module_no, COUNT(*) FROM lesson_catalog
            WHERE course_id = 2 GROUP BY module_no ORDER BY module_no
        """)
        print("\n📊 Уроков по модулям:")
        for row in cursor.fetchall():
            print(f"   Модуль {row[0]}: {row[1]} уроков")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    load_lessons()
