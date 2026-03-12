-- =============================================================================
-- МИГРАЦИЯ: Добавление системы курсов
-- =============================================================================

-- 1. СОЗДАЕМ ТАБЛИЦУ КУРСОВ
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    lessons_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. ВСТАВЛЯЕМ СУЩЕСТВУЮЩИЕ КУРСЫ
INSERT OR IGNORE INTO courses (id, name, description, lessons_count) VALUES 
(1, 'Промт-инженерия', 'Базовый курс по работе с AI-промптами', 23),
(2, 'Vibe Coding', 'Создание Telegram-ботов с AI', 21);

-- 3. ДОБАВЛЯЕМ course_id В ТАБЛИЦУ lessons
ALTER TABLE lessons ADD COLUMN course_id INTEGER DEFAULT 1 REFERENCES courses(id);

-- 4. ОБНОВЛЯЕМ ВСЕ СУЩЕСТВУЮЩИЕ УРОКИ (они из Промт-инженерии)
UPDATE lessons SET course_id = 1 WHERE course_id IS NULL;

-- 5. СОЗДАЕМ ИНДЕКС ДЛЯ БЫСТРОГО ПОИСКА
CREATE INDEX IF NOT EXISTS idx_lessons_course ON lessons(course_id);

-- 6. ПРОВЕРКА
SELECT 
    c.name as курс,
    COUNT(l.id) as уроков
FROM courses c
LEFT JOIN lessons l ON c.id = l.course_id
GROUP BY c.id;