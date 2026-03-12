"""
Скрипт загрузки тестов в базу данных
Автоматически парсит tests_all_complete.txt и загружает в bot.db
"""

import sqlite3
import json
import re
import os

def parse_tests_file(filepath):
    """Парсит файл с тестами и возвращает список тестов"""
    
    tests = []
    current_module = None
    current_lesson = None
    current_test = None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Определяем модуль и урок
        if line.startswith("МОДУЛЬ") and "УРОК" in line:
            # Пример: "МОДУЛЬ 1, УРОК 1"
            match = re.search(r'МОДУЛЬ\s+(\d+).*УРОК\s+(\d+)', line)
            if match:
                current_module = int(match.group(1))
                current_lesson = int(match.group(2))
        
        # Начало теста
        elif line.startswith("Тест") and ":" in line:
            test_num = int(re.search(r'Тест\s+(\d+)', line).group(1))
            
            # Читаем вопрос
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("Вопрос:"):
                i += 1
            question = lines[i].strip().replace("Вопрос: ", "")
            
            # Читаем варианты ответов
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("Варианты:"):
                i += 1
            variants_line = lines[i].strip().replace("Варианты: ", "")
            
            # Парсим варианты (формат: "1) Текст | 2) Текст | 3) Текст")
            options = []
            parts = variants_line.split(" | ")
            for part in parts:
                # Убираем номер в начале (например "1) ")
                option_text = re.sub(r'^\d+\)\s*', '', part.strip())
                options.append(option_text)
            
            # Читаем правильный ответ
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("Правильный ответ"):
                i += 1
            
            correct_line = lines[i].strip()
            
            # Проверяем множественный выбор
            is_multiple = "ответы:" in correct_line.lower()
            
            if is_multiple:
                # Формат: "Правильные ответы: 1,2,4"
                correct_str = re.search(r':\s*(.+)$', correct_line).group(1).strip()
                correct_answers = [int(x.strip()) for x in correct_str.split(',')]
            else:
                # Формат: "Правильный ответ: 2"
                correct_answers = [int(re.search(r':\s*(\d+)', correct_line).group(1))]
            
            # Читаем объяснения
            explanations = {}
            i += 1
            
            while i < len(lines):
                line = lines[i].strip()
                
                # Если начался новый тест или модуль - выходим
                if line.startswith("Тест") or line.startswith("МОДУЛЬ") or line.startswith("===="):
                    break
                
                # Объяснение (формат: "Объяснение 1: Текст")
                if line.startswith("Объяснение"):
                    match = re.search(r'Объяснение\s+(\d+):\s*(.+)', line)
                    if match:
                        exp_num = match.group(1)
                        exp_text = match.group(2)
                        explanations[exp_num] = exp_text
                
                i += 1
            
            # Добавляем тест
            if current_module and current_lesson:
                tests.append({
                    'module_no': current_module,
                    'lesson_no': current_lesson,
                    'question_number': test_num,
                    'question_text': question,
                    'options': options,
                    'correct_answers': correct_answers,
                    'explanations': explanations,
                    'is_multiple_choice': is_multiple
                })
            
            continue
        
        i += 1
    
    return tests


def create_tables(conn):
    """Создает таблицы если их нет"""
    
    cursor = conn.cursor()
    
    # Таблица тестов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_no INTEGER NOT NULL,
            lesson_no INTEGER NOT NULL,
            question_number INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            options TEXT NOT NULL,
            correct_answers TEXT NOT NULL,
            explanations TEXT NOT NULL,
            is_multiple_choice BOOLEAN DEFAULT 0,
            UNIQUE(module_no, lesson_no, question_number)
        )
    """)
    
    # Таблица попыток
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_test_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            module_no INTEGER NOT NULL,
            lesson_no INTEGER NOT NULL,
            attempt_number INTEGER DEFAULT 1,
            answers TEXT,
            score INTEGER DEFAULT 0,
            passed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Индексы
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tests_lesson ON tests(module_no, lesson_no)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_user ON user_test_attempts(user_id, module_no, lesson_no)")
    
    conn.commit()


def load_tests_to_db(tests, conn):
    """Загружает тесты в базу данных"""
    
    cursor = conn.cursor()
    
    loaded = 0
    skipped = 0
    
    for test in tests:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO tests 
                (module_no, lesson_no, question_number, question_text, options, correct_answers, explanations, is_multiple_choice)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test['module_no'],
                test['lesson_no'],
                test['question_number'],
                test['question_text'],
                json.dumps(test['options'], ensure_ascii=False),
                json.dumps(test['correct_answers'], ensure_ascii=False),
                json.dumps(test['explanations'], ensure_ascii=False),
                1 if test['is_multiple_choice'] else 0
            ))
            loaded += 1
        except Exception as e:
            print(f"❌ Ошибка при загрузке теста Модуль {test['module_no']}, Урок {test['lesson_no']}, Тест {test['question_number']}: {e}")
            skipped += 1
    
    conn.commit()
    
    return loaded, skipped


def main():
    """Основная функция"""
    
    # Пути к файлам
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_dir, 'data')
    
    tests_file = os.path.join(data_dir, 'tests_all_complete.txt')
    db_file = os.path.join(data_dir, 'bot.db')
    
    print("=" * 60)
    print("📚 ЗАГРУЗКА ТЕСТОВ В БАЗУ ДАННЫХ")
    print("=" * 60)
    print(f"\n📁 Файл с тестами: {tests_file}")
    print(f"🗃️  База данных: {db_file}\n")
    
    # Проверка файлов
    if not os.path.exists(tests_file):
        print(f"❌ Файл {tests_file} не найден!")
        print(f"   Положите файл tests_all_complete.txt в папку {data_dir}")
        return
    
    if not os.path.exists(db_file):
        print(f"❌ База данных {db_file} не найдена!")
        return
    
    # Парсинг тестов
    print("🔄 Парсинг файла с тестами...")
    tests = parse_tests_file(tests_file)
    print(f"✅ Найдено тестов: {len(tests)}\n")
    
    # Подключение к БД
    print("🔄 Подключение к базе данных...")
    conn = sqlite3.connect(db_file)
    
    # Создание таблиц
    print("🔄 Создание таблиц (если нужно)...")
    create_tables(conn)
    
    # Загрузка тестов
    print("🔄 Загрузка тестов в базу данных...\n")
    loaded, skipped = load_tests_to_db(tests, conn)
    
    # Проверка загрузки
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tests")
    total_in_db = cursor.fetchone()[0]
    
    cursor.execute("SELECT module_no, lesson_no, COUNT(*) FROM tests GROUP BY module_no, lesson_no ORDER BY module_no, lesson_no")
    lessons_stats = cursor.fetchall()
    
    conn.close()
    
    # Итоги
    print("=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ЗАГРУЗКИ")
    print("=" * 60)
    print(f"\n✅ Загружено тестов: {loaded}")
    print(f"⏭️  Пропущено: {skipped}")
    print(f"📚 Всего в базе: {total_in_db}\n")
    
    print("📋 Распределение по урокам:")
    print("-" * 60)
    
    for module, lesson, count in lessons_stats:
        print(f"   Модуль {module}, Урок {lesson}: {count} тестов")
    
    print("\n" + "=" * 60)
    print("✅ ЗАГРУЗКА ЗАВЕРШЕНА!")
    print("=" * 60)


if __name__ == "__main__":
    main()
