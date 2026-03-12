import sqlite3
import re

# Подключение к БД
conn = sqlite3.connect('data/bot.db')
cursor = conn.cursor()

# Создаём таблицу с ПРАВИЛЬНЫМИ колонками
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

# Очищаем старые тесты
cursor.execute('DELETE FROM tests')
conn.commit()

# Читаем файл
with open('data/tests_all_complete.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Разбиваем по урокам
lessons = re.split(r'МОДУЛЬ \d+, УРОК (\d+)', content)

total = 0
current_module = 0

for i in range(1, len(lessons), 2):
    lesson_no = int(lessons[i])
    lesson_content = lessons[i + 1]
    
    # Определяем модуль по номеру урока
    if 1 <= lesson_no <= 5:
        current_module = 1
    elif 6 <= lesson_no <= 11:
        current_module = 2
    elif 12 <= lesson_no <= 15:
        current_module = 3
    elif 16 <= lesson_no <= 20:
        current_module = 4
    elif 21 <= lesson_no <= 23:
        current_module = 5
    
    # Ищем тесты
    tests = re.findall(
        r'Тест (\d+):\s*\n'
        r'Вопрос: (.+?)\n'
        r'Варианты: (.+?)\n'
        r'Правильны[йе] ответ[ы]?: (.+?)\n'
        r'(Объяснение.+?)(?=Тест \d+:|МОДУЛЬ|====)',
        lesson_content,
        re.DOTALL
    )
    
    for test_no, question, variants_str, correct_str, explanations_str in tests:
        # Парсим варианты в СПИСОК
        options = []
        for match in re.finditer(r'(\d+)\) ([^|]+)', variants_str):
            options.append(match.group(2).strip())
        
        # Парсим правильные ответы
        correct_answers = [int(x.strip()) for x in correct_str.replace(',', ' ').split()]
        
        # Парсим объяснения в СЛОВАРЬ
        explanations = {}
        for match in re.finditer(r'Объяснение (\d+): (.+?)(?=Объяснение \d+:|$)', explanations_str, re.DOTALL):
            explanations[match.group(1)] = match.group(2).strip()
        
        # Импортируем json для сериализации
        import json
        
        # Вставляем в БД с ПРАВИЛЬНЫМИ названиями колонок
        cursor.execute('''
            INSERT INTO tests (module_no, lesson_no, question_number, question_text, options, correct_answers, explanations, is_multiple_choice)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_module,
            lesson_no,
            int(test_no),
            question.strip(),
            json.dumps(options, ensure_ascii=False),
            json.dumps(correct_answers, ensure_ascii=False),
            json.dumps(explanations, ensure_ascii=False),
            1 if len(correct_answers) > 1 else 0
        ))
        
        total += 1
        print(f'✅ Модуль {current_module} | Урок {lesson_no} | Тест {test_no}')

conn.commit()
conn.close()

print(f'\n🎉 Загружено тестов: {total}')