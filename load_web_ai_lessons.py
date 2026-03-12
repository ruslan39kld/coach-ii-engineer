"""
Скрипт регистрации уроков курса 3 (Web AI / Нейросети для работы) в базе данных.
Файлы уроков хранятся локально — содержимое в БД не загружается,
регистрируются только метаданные: module_no, lesson_no, title, path, course_id=3.

Правильная структура курса 3:
  МОДУЛЬ 1: уроки 1–4
  МОДУЛЬ 2: уроки 5–9
  МОДУЛЬ 3: уроки 10–13
  МОДУЛЬ 4: уроки 14–16
  МОДУЛЬ 5: уроки 17–18
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

# --------------------------------------------------------------------------
# Маппинг: (module_no, lesson_no) → (title, filename)
# --------------------------------------------------------------------------
LESSONS_MAPPING = {
    # МОДУЛЬ 1 (уроки 1–4)
    (1,  1): ("Введение в нейросети и ИИ-инструменты",             "urok1_web_ai.txt"),
    (1,  2): ("Как выбрать нейросеть под задачу",                   "urok2_web_ai.txt"),
    (1,  3): ("Текстовые нейросети: обзор и сравнение",             "urok3_web_ai.txt"),
    (1,  4): ("Регистрация и первые шаги в ИИ-сервисах",            "urok4_web_ai.txt"),

    # МОДУЛЬ 2 (уроки 5–9)
    (2,  5): ("YandexGPT и GigaChat: российские ИИ на практике",    "urok5_web_ai.txt"),
    (2,  6): ("ChatGPT, Claude, Gemini: зарубежные ИИ",             "urok6_web_ai.txt"),
    (2,  7): ("DeepSeek, Kimi, Qwen и Perplexity",                  "urok7_web_ai.txt"),
    (2,  8): ("Промпт-инжиниринг: основные техники",                 "urok8_web_ai.txt"),
    (2,  9): ("ИИ для анализа документов и данных",                  "urok9_web_ai.txt"),

    # МОДУЛЬ 3 (уроки 10–13)
    (3, 10): ("Нейросети для генерации изображений: обзор",         "urok10_web_ai.txt"),
    (3, 11): ("Российские генераторы: Шедеврум, Кандинский",        "urok11_web_ai.txt"),
    (3, 12): ("Зарубежные генераторы: Flux, Midjourney, DALL-E",    "urok12_web_ai.txt"),
    (3, 13): ("Создание изображений: практика и промпты",           "urok13_web_ai.txt"),

    # МОДУЛЬ 4 (уроки 14–16)
    (4, 14): ("Нейросети для видеогенерации: обзор",                "urok14_web_ai.txt"),
    (4, 15): ("Видеогенераторы: российские и зарубежные решения",   "urok15_web_ai.txt"),
    (4, 16): ("Создание видеоконтента с помощью ИИ: практика",      "urok16_web_ai.txt"),

    # МОДУЛЬ 5 (уроки 17–18)
    (5, 17): ("ИИ для аудио, музыки и голоса",                      "urok17_web_ai.txt"),
    (5, 18): ("Итоговый проект: комплексное применение ИИ",         "urok18_web_ai.txt"),
}


def load_web_ai_lessons(source_folder: str):
    """Регистрирует уроки курса 3 (Web AI) в базе данных."""
    db = Database(config.DB_PATH)

    logging.info("Начало регистрации уроков курса 3 (Web AI)...")

    total_lessons = 0
    errors = 0

    for (module_no, lesson_no), (title, filename) in LESSONS_MAPPING.items():
        file_path = os.path.join(source_folder, filename)

        if not os.path.exists(file_path):
            logging.warning(f"Файл не найден (пропускаем): {file_path}")
            errors += 1
            continue

        try:
            db.add_lesson_to_catalog(
                m_no=module_no,
                l_no=lesson_no,
                title=title,
                path=file_path,
                content="",      # содержимое не загружается в БД
                course_id=3      # ← курс 3: Web AI
            )

            logging.info(f"Модуль {module_no} | Урок {lesson_no:2d}: {title}")
            total_lessons += 1

        except Exception as e:
            logging.error(f"Ошибка при регистрации урока {lesson_no}: {e}")
            errors += 1

    logging.info(f"Зарегистрировано уроков: {total_lessons}")
    if errors:
        logging.warning(f"Предупреждений/ошибок: {errors}")
    else:
        logging.info("Все уроки успешно зарегистрированы!")

    logging.info("База курса Web AI готова.")


if __name__ == "__main__":
    # Укажите путь к папке с файлами уроков
    SOURCE_FOLDER = "/mnt/user-data/web_ai_lessons"

    load_web_ai_lessons(SOURCE_FOLDER)
