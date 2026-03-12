import sqlite3
import re
import json

# Подключение к БД
conn = sqlite3.connect('data/bot.db')
cursor = conn.cursor()

# Создаём таблицу если не существует
cursor.execute('''
CREATE TABLE IF NOT EXISTS tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_no INTEGER,
    lesson_no INTEGER,
    question_number INTEGER,
    question_text TEXT,
    options TEXT,
    correct_answers TEXT,
    explanations TEXT,
    is_multiple_choice INTEGER DEFAULT 0
)
''')

# Удаляем только тесты курса 3 (модули 6-10)
cursor.execute('DELETE FROM tests WHERE module_no BETWEEN 6 AND 10')
deleted = cursor.rowcount
conn.commit()
print(f'🗑️  Удалено старых тестов курса 3: {deleted}')

# Читаем файл
with open('data/tests_all_complete.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Разбиваем по заголовкам МОДУЛЬ X, УРОК Y
# Формат: "МОДУЛЬ 6, УРОК 1"
parts = re.split(r'МОДУЛЬ\s+(\d+),\s*УРОК\s+(\d+)', content)

total = 0
errors = 0

# parts[0] — текст до первого заголовка (игнорируем)
# далее тройками: (module_no, lesson_no, content)
for i in range(1, len(parts), 3):
    module_no = int(parts[i])
    lesson_no = int(parts[i + 1])
    lesson_content = parts[i + 2]

    # Валидация: только модули 6-10
    if not (6 <= module_no <= 10):
        print(f'⚠️  Пропускаем модуль {module_no} (не в диапазоне 6-10)')
        continue

    # Ищем тесты внутри блока урока
    tests = re.findall(
        r'Тест\s+(\d+):\s*\n'
        r'Вопрос:\s*(.+?)\n'
        r'Варианты:\s*(.+?)\n'
        r'Правильны[йе]\s+ответ[ы]?:\s*(.+?)\n'
        r'(Объяснение.+?)(?=Тест\s+\d+:|МОДУЛЬ\s+\d+|={4,}|\Z)',
        lesson_content,
        re.DOTALL
    )

    if not tests:
        print(f'⚠️  Модуль {module_no} | Урок {lesson_no} — тестов не найдено')
        continue

    for test_no, question, variants_str, correct_str, explanations_str in tests:
        try:
            # Парсим варианты: "1) Вариант А | 2) Вариант Б | ..."
            options = []
            for match in re.finditer(r'(\d+)\)\s*([^|]+)', variants_str):
                options.append(match.group(2).strip())

            if not options:
                print(f'❌  Модуль {module_no} | Урок {lesson_no} | Тест {test_no} — нет вариантов')
                errors += 1
                continue

            # Парсим правильные ответы: "1" или "1, 2"
            correct_answers = [int(x.strip()) for x in correct_str.replace(',', ' ').split() if x.strip().isdigit()]

            if not correct_answers:
                print(f'❌  Модуль {module_no} | Урок {lesson_no} | Тест {test_no} — нет правильных ответов')
                errors += 1
                continue

            # Парсим объяснения: "Объяснение 1: текст\nОбъяснение 2: текст"
            explanations = {}
            for match in re.finditer(
                r'Объяснение\s+(\d+):\s*(.+?)(?=Объяснение\s+\d+:|$)',
                explanations_str,
                re.DOTALL
            ):
                explanations[match.group(1)] = match.group(2).strip()

            # Вставляем в БД
            cursor.execute('''
                INSERT INTO tests (module_no, lesson_no, question_number, question_text,
                                   options, correct_answers, explanations, is_multiple_choice)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                module_no,
                lesson_no,
                int(test_no),
                question.strip(),
                json.dumps(options, ensure_ascii=False),
                json.dumps(correct_answers, ensure_ascii=False),
                json.dumps(explanations, ensure_ascii=False),
                1 if len(correct_answers) > 1 else 0
            ))

            total += 1
            print(f'✅ Модуль {module_no} | Урок {lesson_no} | Тест {test_no}')

        except Exception as e:
            print(f'❌  Модуль {module_no} | Урок {lesson_no} | Тест {test_no} — ошибка: {e}')
            errors += 1

conn.commit()
conn.close()

print(f'\n{"="*50}')
print(f'🎉 Загружено тестов: {total}')
if errors:
    print(f'⚠️  Ошибок: {errors}')
print(f'{"="*50}')
