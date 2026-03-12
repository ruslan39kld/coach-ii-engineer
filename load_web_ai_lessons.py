"""
Скрипт загрузки уроков Web AI в базу данных
Загружает 18 уроков из папки outputs для курса 3 (Web AI)
"""

import os
import sys
import logging

# Добавляем папку src в путь импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.database import Database
import config

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Маппинг файлов уроков
LESSONS_MAPPING = {
    # МОДУЛЬ 1: Основы Web AI разработки (4 урока)
    (1, 1): ("Введение в Web AI разработку", "urok1_web_ai_improved.txt"),
    (1, 2): ("Инструменты и стек технологий", "urok2_web_ai_improved.txt"),
    (1, 3): ("Архитектура веб-приложений с AI", "urok3_web_ai_improved.txt"),
    (1, 4): ("Настройка рабочего окружения", "urok4_web_ai_improved.txt"),

    # МОДУЛЬ 2: Фронтенд с AI (5 уроков)
    (2, 5): ("HTML и CSS с AI-помощником", "urok5_web_ai_improved.txt"),
    (2, 6): ("JavaScript и AI API", "urok6_web_ai_improved.txt"),
    (2, 7): ("Создание интерактивного интерфейса", "urok7_web_ai_improved.txt"),
    (2, 8): ("Работа с AI-чат-виджетами", "urok8_web_ai_improved.txt"),
    (2, 9): ("Адаптивный дизайн с AI", "urok9_web_ai_improved.txt"),

    # МОДУЛЬ 3: Бэкенд с AI (5 уроков)
    (3, 10): ("FastAPI и интеграция AI", "urok10_web_ai_improved.txt"),
    (3, 11): ("REST API для AI-приложений", "urok11_web_ai_improved.txt"),
    (3, 12): ("Работа с базами данных", "urok12_web_ai_improved.txt"),
    (3, 13): ("Аутентификация и безопасность", "urok13_web_ai_improved.txt"),
    (3, 14): ("AI-функциональность на сервере", "urok14_web_ai_improved.txt"),

    # МОДУЛЬ 4: Деплой и Production (4 урока)
    (4, 15): ("Подготовка к деплою", "urok15_web_ai_improved.txt"),
    (4, 16): ("Деплой веб-приложения с AI", "urok16_web_ai_improved.txt"),
    (4, 17): ("Мониторинг и оптимизация", "urok17_web_ai_improved.txt"),
    (4, 18): ("Финальный проект – ваше Web AI приложение", "urok18_web_ai_improved.txt"),
}


def load_web_ai_lessons(source_folder: str):
    """Загрузка уроков Web AI в базу данных"""
    db = Database(config.DB_PATH)

    logging.info("🚀 Начало загрузки уроков Web AI...")

    total_lessons = 0
    errors = 0

    for (module_no, lesson_no), (title, filename) in LESSONS_MAPPING.items():
        file_path = os.path.join(source_folder, filename)

        if not os.path.exists(file_path):
            logging.error(f"❌ Файл не найден: {file_path}")
            errors += 1
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Сохраняем в БД с course_id=3
            db.add_lesson_to_catalog(
                m_no=module_no,
                l_no=lesson_no,
                title=title,
                path=file_path,
                content=content,
                course_id=3  # ← Web AI
            )

            logging.info(f"✅ Модуль {module_no} | Урок {lesson_no}: {title}")
            total_lessons += 1

        except Exception as e:
            logging.error(f"❌ Ошибка при обработке {file_path}: {e}")
            errors += 1

    logging.info(f"\n✨ Загружено уроков: {total_lessons}")
    if errors > 0:
        logging.warning(f"⚠️ Ошибок: {errors}")
    else:
        logging.info("✅ Все уроки успешно загружены!")

    logging.info("База курса Web AI готова!")


if __name__ == "__main__":
    # Путь к папке с улучшенными уроками
    SOURCE_FOLDER = "/mnt/user-data/outputs"

    # Альтернативно можно указать путь на Windows
    # SOURCE_FOLDER = r"C:\Users\BeltiugovRV\Desktop\Промтинг\outputs"

    load_web_ai_lessons(SOURCE_FOLDER)
