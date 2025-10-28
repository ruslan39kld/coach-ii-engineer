# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('data/bot.db')
cursor = conn.cursor()

# Total count
cursor.execute('SELECT COUNT(*) FROM faq')
total = cursor.fetchone()[0]
print(f'Total questions in DB: {total}')

# Sample questions
cursor.execute('SELECT question, answer, source_file FROM faq LIMIT 3')
print('\nSample questions:')
for i, (q, a, src) in enumerate(cursor.fetchall(), 1):
    print(f'\n{i}. Question: {q[:80]}...')
    print(f'   Answer: {a[:80]}...')
    print(f'   Source: {src}')

# Top files
cursor.execute('SELECT source_file, COUNT(*) as cnt FROM faq GROUP BY source_file ORDER BY cnt DESC LIMIT 5')
print('\n\nTop 5 files by question count:')
for src, cnt in cursor.fetchall():
    print(f'  {cnt} questions - {src}')

conn.close()
