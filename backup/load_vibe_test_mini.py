import sqlite3
import json

conn = sqlite3.connect('data/bot.db')
cursor = conn.cursor()
total_loaded = 0

module_6_tests = [
    {"module_no": 6, "lesson_no": 1, "question_number": 1, "question_text": "Что такое Vibe Coding?", "options": ["Методология быстрой разработки с использованием ИИ-ассистентов", "Название конкретной нейросети для программирования", "Стиль написания кода с особым форматированием", "Библиотека Python для создания ботов"], "correct_answers": [1], "explanations": {"1": "✅ Правильно! Vibe Coding — это методология работы, где вы выступаете архитектором, а ИИ — исполнителем кода.", "2": "Неверно. Vibe Coding — это не конкретный инструмент, а методология работы с ИИ.", "3": "Неверно. Это не про стиль кода, а про способ разработки с помощью ИИ.", "4": "Неверно. Vibe Coding — методология, а не библиотека."}, "is_multiple_choice": 0},
    {"module_no": 6, "lesson_no": 1, "question_number": 2, "question_text": "Какая ваша роль при использовании Vibe Coding?", "options": ["Программист, который пишет весь код самостоятельно", "Архитектор решения, который ставит задачи ИИ", "Тестировщик готовых решений от ИИ", "Наблюдатель за работой нейросети"], "correct_answers": [2], "explanations": {"1": "Неверно. Vibe Coding предполагает делегирование написания кода ИИ, а не самостоятельное программирование.", "2": "✅ Правильно! Вы проектируете архитектуру и ставите задачи, а ИИ выполняет техническую реализацию.", "3": "Неверно. Роль шире — вы проектируете решение и управляете процессом, а не только тестируете.", "4": "Неверно. Вы активно участвуете в процессе, управляя ИИ, а не просто наблюдаете."}, "is_multiple_choice": 0},
    {"module_no": 6, "lesson_no": 1, "question_number": 3, "question_text": "Для кого подходит курс Vibe Coding?", "options": ["Только для профессиональных программистов", "Только для людей с техническим образованием", "Для всех, кто хочет создавать ботов без глубоких знаний программирования", "Только для специалистов по Data Science"], "correct_answers": [3], "explanations": {"1": "Неверно. Курс специально создан для людей БЕЗ глубоких знаний программирования.", "2": "Неверно. Техническое образование не требуется — курс объясняет все простым языком.", "3": "✅ Правильно! Курс подходит для любых специалистов, желающих автоматизировать задачи с помощью ботов.", "4": "Неверно. Курс универсален и не требует специализации в Data Science."}, "is_multiple_choice": 0}
]

for test in module_6_tests:
    cursor.execute('INSERT INTO tests (module_no, lesson_no, question_number, question_text, options, correct_answers, explanations, is_multiple_choice) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (test['module_no'], test['lesson_no'], test['question_number'], test['question_text'], json.dumps(test['options'], ensure_ascii=False), json.dumps(test['correct_answers']), json.dumps(test['explanations'], ensure_ascii=False), test['is_multiple_choice']))
    total_loaded += 1

conn.commit()
print(f'✅ Модуль 6: загружено {len(module_6_tests)} тестов')
print(f'📊 Всего загружено: {total_loaded} тестов')
conn.close()
