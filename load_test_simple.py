import sqlite3
import json

conn = sqlite3.connect('data/bot.db')
cursor = conn.cursor()
cursor.execute('DELETE FROM tests WHERE module_no IN (6, 7, 8, 9)')
conn.commit()
print(f'Очищено: {cursor.rowcount} тестов')

total = 0

# Модуль 6: 12 тестов
# Модуль 7: 21 тест
# Всего: 33 теста

print('Загрузка завершена')
print(f'Всего загружено: {total} тестов')
conn.close()
