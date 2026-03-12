import sqlite3
import os

DB_PATH = "data/bot.db"
LESSONS_DIR = r"C:\Users\BeltiugovRV\Desktop\Промтинг\БАЗА\Вайб кодинг"

# Структура курса: модуль → уроки
COURSE_STRUCTURE = {
    "МОДУЛЬ 1 ОСНОВЫ VIBE CODING": {
        "module_number": 1,
        "lessons": [
            "УРОК 1 Что такое Vibe Coding и зачем он вам нужен",
            "УРОК 2 Возможности Vibe Coding – что можно создавать",
            "УРОК 3 Технические основы простыми словами"
        ]
    },
    "МОДУЛЬ 2 НАСТРОЙКА СРЕДЫ И ПЕРВЫЙ БОТ": {
        "module_number": 2,
        "lessons": [
            "УРОК 4 Настройка окружения",
            "УРОК 5 Регистрация бота в Telegram",
            "УРОК 6 Hello World – первый работающий бот",
            "УРОК 7 Добавление кнопок и меню",
            "УРОК 8 Работа с состояниями (FSM)",
            "УРОК 9 Первая база данных (SQLite)"
        ]
    },
    "МОДУЛЬ 3 ПРОДВИНУТЫЕ ВОЗМОЖНОСТИ": {
        "module_number": 3,
        "lessons": [
            "УРОК 10 Регистрация в GigaChat",
            "УРОК 11 Интеграция бота с GigaChat",
            "УРОК 12 Настройка промптов для бота",
            "УРОК 13 Работа с документами",
            "УРОК 14 База знаний и RAG"
        ]
    },
    "МОДУЛЬ 4 ДЕПЛОЙ И PRODUCTION": {
        "module_number": 4,
        "lessons": [
            "УРОК 15 Улучшение точности ответов",
            "УРОК 16 Логирование и мониторинг",
            "УРОК 17 Деплой бота на сервер",
            "УРОК 18 Обновление без простоя",
            "УРОК 19 Оптимизация и масштабирование",
            "УРОК 20 Финальный проект"
        ]
    }
}

def find_lesson_file(lesson_number):
    """Ищет файл урока по номеру"""
    for root, dirs, files in os.walk(LESSONS_DIR):
        for file in files:
            if file.startswith(f"urok{lesson_number}_") and file.endswith(".txt"):
                return os.path.join(root, file)
    return None

def load_lessons():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    lesson_number = 1
    loaded_count = 0
    
    print("📚 Начинаем загрузку уроков Vibe Coding...\n")
    
    try:
        for module_name, module_data in COURSE_STRUCTURE.items():
            module_num = module_data["module_number"]
            print(f"📂 {module_name}")
            
            for lesson_title in module_data["lessons"]:
                # Ищем файл урока
                file_path = find_lesson_file(lesson_number)
                
                if not file_path:
                    print(f"   ⚠️  УРОК {lesson_number}: файл не найден - {lesson_title}")
                    lesson_number += 1
                    continue
                
                # Читаем содержимое
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Вставляем в БД
                cursor.execute("""
                    INSERT INTO lesson_catalog (
                        title, 
                        content, 
                        module_no, 
                        lesson_no,
                        course_id
                    ) VALUES (?, ?, ?, ?, 2)
                """, (lesson_title, content, module_num, lesson_number))
                print(f"   ✅ УРОК {lesson_number}: {lesson_title[:50]}...")
                loaded_count += 1
                lesson_number += 1
        
        # Добавляем финальный проект (урок 21)
        file_path = find_lesson_file(21)
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            cursor.execute("""
                INSERT INTO lesson_catalog (
                    title, 
                    content, 
                    module_no, 
                    lesson_no,
                    course_id
                ) VALUES (?, ?, ?, ?, 2)
            """, ("УРОК 21 Финальный проект", content, 4, 21))
            
            print(f"\n   ✅ УРОК 21: Финальный проект")
            loaded_count += 1
        
        conn.commit()
        
        print(f"\n🎉 УСПЕХ! Загружено {loaded_count} уроков!")
        
        # Проверка
        cursor.execute("""
            SELECT c.name, COUNT(l.id)
            FROM courses c
            LEFT JOIN lesson_catalog l ON c.id = l.course_id
            GROUP BY c.id
        """)
        
        print("\n📊 Итоговая статистика:")
        for row in cursor.fetchall():
            print(f"   {row[0]}: {row[1]} уроков")
            
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    load_lessons()