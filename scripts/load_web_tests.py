"""
Парсер тестов для веб-курса (модули 6-10).

Формат входных файлов (data/web_tests/tests_web_module_1.txt ... tests_web_module_5.txt):

    УРОК 1: Название урока

    ВОПРОС 1
    Текст вопроса?

    1. Вариант один
    2. Вариант два ✅
    3. Вариант три
    4. Вариант четыре

    Пояснения:
    1 ❌ Текст пояснения...
    2 ✅ Верно! Текст пояснения...
    3 ❌ Текст пояснения...
    4 ❌ Текст пояснения...

    ВОПРОС 2
    ...

    УРОК 2: Название урока
    ...

Правила:
- Правильный ответ определяется по символу ✅ в строке варианта.
- Уроки разделяются строкой «УРОК X: Название».
- Файл 1 → module_no=6, файл 2 → module_no=7, ..., файл 5 → module_no=10.
- lesson_no берётся из заголовка «УРОК X:».
"""

import json
import re
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "bot.db"
DATA_DIR = Path(__file__).parent.parent / "data" / "web_tests"

# Смещение: файл N → module_no = N + 5
MODULE_OFFSET = 5


def parse_options_and_correct(lines: list[str]) -> tuple[list[str], list[int]]:
    """
    Парсит строки вариантов ответа.
    Возвращает (options, correct_answers).
    options  — список текстов без ✅
    correct_answers — список 1-based индексов правильных ответов
    """
    options = []
    correct = []
    for line in lines:
        m = re.match(r'^(\d+)\.\s+(.+)$', line.strip())
        if not m:
            continue
        idx = int(m.group(1))
        text = m.group(2).strip()
        is_correct = '✅' in text
        text = text.replace('✅', '').strip()
        options.append(text)
        if is_correct:
            correct.append(idx)
    return options, correct


def parse_explanations(lines: list[str]) -> dict[str, str]:
    """
    Парсит блок пояснений.
    Формат строк: «N ✅ текст» или «N ❌ текст» (могут продолжаться на следующих строках).
    Возвращает словарь {"1": "текст", "2": "текст", ...}.
    """
    explanations: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    for line in lines:
        m = re.match(r'^(\d+)\s+[✅❌]\s*(.*)', line.strip())
        if m:
            # Сохраняем предыдущее пояснение
            if current_key is not None:
                explanations[current_key] = ' '.join(current_lines).strip()
            current_key = m.group(1)
            current_lines = [m.group(2).strip()] if m.group(2).strip() else []
        elif current_key is not None and line.strip():
            current_lines.append(line.strip())

    if current_key is not None:
        explanations[current_key] = ' '.join(current_lines).strip()

    return explanations


def parse_question_block(block: str) -> dict | None:
    """
    Парсит один блок «ВОПРОС N ... Пояснения: ...».
    Возвращает dict с полями: question_number, question_text, options,
    correct_answers, explanations, is_multiple_choice.
    Возвращает None если блок пустой или не распознан.
    """
    lines = block.strip().splitlines()
    if not lines:
        return None

    # Первая строка — номер вопроса (уже отрезан снаружи)
    # Ищем разделитель «Пояснения:»
    try:
        expl_idx = next(
            i for i, l in enumerate(lines) if re.match(r'^Пояснения\s*:', l.strip())
        )
    except StopIteration:
        expl_idx = len(lines)

    body_lines = lines[:expl_idx]
    expl_lines = lines[expl_idx + 1:]

    # Первая непустая строка — текст вопроса
    question_text = ''
    option_lines = []
    reading_options = False

    for line in body_lines:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r'^\d+\.', stripped):
            reading_options = True
        if reading_options:
            option_lines.append(stripped)
        elif not question_text:
            question_text = stripped
        else:
            # Продолжение текста вопроса (многострочный вопрос)
            question_text += ' ' + stripped

    if not question_text:
        return None

    options, correct_answers = parse_options_and_correct(option_lines)
    explanations = parse_explanations(expl_lines)

    return {
        'question_text': question_text,
        'options': options,
        'correct_answers': correct_answers,
        'explanations': explanations,
        'is_multiple_choice': 1 if len(correct_answers) > 1 else 0,
    }


def parse_lesson_block(lesson_header: str, lesson_body: str) -> tuple[int, list[dict]]:
    """
    Парсит один блок урока.
    Возвращает (lesson_no, questions).
    """
    m = re.match(r'УРОК\s+(\d+)\s*:', lesson_header.strip())
    lesson_no = int(m.group(1)) if m else 0

    # Разбиваем по «ВОПРОС N»
    parts = re.split(r'(?m)^ВОПРОС\s+(\d+)\s*$', lesson_body)
    # parts = [text_before_first_question, q_no, q_body, q_no, q_body, ...]

    questions = []
    for i in range(1, len(parts), 2):
        q_no = int(parts[i])
        q_body = parts[i + 1] if i + 1 < len(parts) else ''
        parsed = parse_question_block(q_body)
        if parsed:
            parsed['question_number'] = q_no
            questions.append(parsed)

    return lesson_no, questions


def parse_file(file_path: Path, module_no: int) -> list[dict]:
    """
    Читает файл и возвращает список записей для вставки в БД.
    """
    content = file_path.read_text(encoding='utf-8')

    # Разбиваем по «УРОК X: ...»
    parts = re.split(r'(?m)^(УРОК\s+\d+\s*:.*)$', content)
    # parts = [text_before_first_lesson, header, body, header, body, ...]

    records = []
    for i in range(1, len(parts), 2):
        header = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ''
        lesson_no, questions = parse_lesson_block(header, body)

        for q in questions:
            records.append({
                'module_no': module_no,
                'lesson_no': lesson_no,
                **q,
            })

    return records


def load_into_db(records: list[dict], cursor: sqlite3.Cursor, module_no: int):
    """Удаляет старые записи модуля и вставляет новые."""
    cursor.execute('DELETE FROM tests WHERE module_no = ?', (module_no,))
    for r in records:
        cursor.execute(
            '''
            INSERT INTO tests
                (module_no, lesson_no, question_number, question_text,
                 options, correct_answers, explanations, is_multiple_choice)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                r['module_no'],
                r['lesson_no'],
                r['question_number'],
                r['question_text'],
                json.dumps(r['options'], ensure_ascii=False),
                json.dumps(r['correct_answers'], ensure_ascii=False),
                json.dumps(r['explanations'], ensure_ascii=False),
                r['is_multiple_choice'],
            ),
        )


def ensure_tests_table(cursor: sqlite3.Cursor):
    cursor.execute(
        '''
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
        '''
    )


def main():
    # Можно передать номера файлов аргументом: python load_web_tests.py 1 3 5
    file_nums = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else list(range(1, 6))

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    ensure_tests_table(cursor)

    total = 0
    for file_num in file_nums:
        module_no = file_num + MODULE_OFFSET
        file_path = DATA_DIR / f'tests_web_module_{file_num}.txt'

        if not file_path.exists():
            print(f'⚠️  Файл не найден: {file_path}')
            continue

        records = parse_file(file_path, module_no)
        load_into_db(records, cursor, module_no)
        conn.commit()

        lesson_counts: dict[int, int] = {}
        for r in records:
            lesson_counts[r['lesson_no']] = lesson_counts.get(r['lesson_no'], 0) + 1

        print(f'\n📦 Модуль {module_no} ← {file_path.name}')
        for lesson_no, count in sorted(lesson_counts.items()):
            print(f'   Урок {lesson_no}: {count} вопрос(ов)')
        total += len(records)

    conn.close()
    print(f'\n🎉 Итого загружено вопросов: {total}')


if __name__ == '__main__':
    main()
