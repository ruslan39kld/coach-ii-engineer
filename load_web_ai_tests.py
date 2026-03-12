"""
Скрипт загрузки тестов курса "Веб-разработка с AI" (course_id=3) в базу данных.

Структура курса:
  Модуль 1 (module_no=11): Введение в веб-разработку с AI — уроки 1-4
  Модуль 2 (module_no=12): Frontend разработка — уроки 5-8
  Модуль 3 (module_no=13): Backend и API — уроки 9-12
  Модуль 4 (module_no=14): AI-интеграция в веб — уроки 13-16
  Модуль 5 (module_no=15): Деплой и production — уроки 17-20

Итого: 20 уроков × 3 теста = 60 тестов
"""

import sqlite3
import json
import os
import sys

# Добавляем текущую папку в путь для импорта файлов тестов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tests_web_module_1 import module_1_tests
from tests_web_module_2 import module_2_tests
from tests_web_module_3 import module_3_tests
from tests_web_module_4 import module_4_tests
from tests_web_module_5 import module_5_tests

COURSE_ID = 3
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'bot.db')


def ensure_course_id_column(cursor):
    """Добавляет колонку course_id в таблицу tests, если её нет"""
    try:
        cursor.execute("ALTER TABLE tests ADD COLUMN course_id INTEGER DEFAULT 1")
        print("✅ Добавлена колонка course_id в таблицу tests")
    except sqlite3.OperationalError:
        pass  # Колонка уже существует


def create_tests_table(cursor):
    """Создаёт таблицу tests, если она не существует"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_no INTEGER NOT NULL,
            lesson_no INTEGER NOT NULL,
            question_number INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            options TEXT NOT NULL,
            correct_answers TEXT NOT NULL,
            explanations TEXT NOT NULL,
            is_multiple_choice INTEGER DEFAULT 0,
            course_id INTEGER DEFAULT 1,
            UNIQUE(course_id, module_no, lesson_no, question_number)
        )
    ''')


def load_module_tests(cursor, tests_list, module_name):
    """Загружает тесты одного модуля в БД"""
    loaded = 0
    skipped = 0

    for test in tests_list:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO tests (
                    module_no, lesson_no, question_number,
                    question_text, options, correct_answers,
                    explanations, is_multiple_choice, course_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                test['module_no'],
                test['lesson_no'],
                test['question_number'],
                test['question_text'],
                json.dumps(test['options'], ensure_ascii=False),
                json.dumps(test['correct_answers'], ensure_ascii=False),
                json.dumps(test['explanations'], ensure_ascii=False),
                test['is_multiple_choice'],
                COURSE_ID
            ))
            print(f"  ✅ Модуль {test['module_no']} | Урок {test['lesson_no']} | Тест {test['question_number']}")
            loaded += 1
        except Exception as e:
            print(f"  ❌ Ошибка: Модуль {test['module_no']}, Урок {test['lesson_no']}, "
                  f"Тест {test['question_number']}: {e}")
            skipped += 1

    print(f"  📊 {module_name}: загружено {loaded}, пропущено {skipped}\n")
    return loaded, skipped


def main():
    print("=" * 60)
    print("🌐 ЗАГРУЗКА ТЕСТОВ КУРСА 'ВЕБ-РАЗРАБОТКА С AI' (course_id=3)")
    print("=" * 60)
    print(f"\n🗃️  База данных: {DB_PATH}\n")

    if not os.path.exists(DB_PATH):
        print(f"❌ База данных не найдена: {DB_PATH}")
        print("   Убедитесь, что бот был запущен хотя бы один раз для создания БД.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Создаём/обновляем таблицу
    create_tests_table(cursor)
    ensure_course_id_column(cursor)
    conn.commit()

    # Удаляем старые тесты курса 3 перед загрузкой
    cursor.execute("DELETE FROM tests WHERE course_id = ?", (COURSE_ID,))
    deleted = cursor.rowcount
    if deleted > 0:
        print(f"🗑️  Удалено старых тестов курса {COURSE_ID}: {deleted}\n")
    conn.commit()

    # Загружаем тесты по модулям
    all_modules = [
        (module_1_tests, "Модуль 1 — Введение в веб-разработку с AI"),
        (module_2_tests, "Модуль 2 — Frontend разработка"),
        (module_3_tests, "Модуль 3 — Backend и API"),
        (module_4_tests, "Модуль 4 — AI-интеграция в веб"),
        (module_5_tests, "Модуль 5 — Деплой и production"),
    ]

    total_loaded = 0
    total_skipped = 0

    for tests_list, name in all_modules:
        print(f"📂 {name}")
        loaded, skipped = load_module_tests(cursor, tests_list, name)
        total_loaded += loaded
        total_skipped += skipped

    conn.commit()

    # Статистика по урокам
    cursor.execute("""
        SELECT module_no, lesson_no, COUNT(*)
        FROM tests
        WHERE course_id = ?
        GROUP BY module_no, lesson_no
        ORDER BY module_no, lesson_no
    """, (COURSE_ID,))
    stats = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM tests WHERE course_id = ?", (COURSE_ID,))
    total_in_db = cursor.fetchone()[0]

    conn.close()

    print("=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ЗАГРУЗКИ")
    print("=" * 60)
    print(f"\n✅ Загружено тестов: {total_loaded}")
    if total_skipped:
        print(f"⏭️  Пропущено: {total_skipped}")
    print(f"📚 Всего в БД (course_id={COURSE_ID}): {total_in_db}\n")

    print("📋 Распределение по урокам:")
    print("-" * 60)
    for module_no, lesson_no, count in stats:
        print(f"   Модуль {module_no}, Урок {lesson_no}: {count} тестов")

    print("\n" + "=" * 60)
    print("✅ ЗАГРУЗКА ЗАВЕРШЕНА!")
    print("=" * 60)


if __name__ == "__main__":
    main()
