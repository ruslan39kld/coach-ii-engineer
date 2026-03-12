"""
Скрипт загрузки уроков Vibe Coding в базу данных
Загружает 20 улучшенных уроков из папки outputs
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
    # МОДУЛЬ 1: Основы Vibe Coding (4 урока)
    (1, 1): ("Что такое Vibe Coding и зачем он вам нужен", "urok1_vibe_coding_improved.txt"),
    (1, 2): ("Возможности Vibe Coding – что можно создавать", "urok2_vibe_coding_improved.txt"),
    (1, 3): ("Технические основы простыми словами", "urok3_vibe_coding_improved.txt"),
    (1, 4): ("Методология Vibe Coding на практике", "urok4_metodologiya_vibe_coding_improved.txt"),
    
    # МОДУЛЬ 2: Создание первого бота (8 уроков) - БЕЗ УРОКА 8 (кнопки удалены)
    (2, 5): ("Настройка рабочей среды – VS Code", "urok5_nastroyka_vscode_improved.txt"),
    (2, 6): ("Регистрация бота в Telegram", "urok6_registratsiya_bota_improved.txt"),
    (2, 7): ("Hello World – первый работающий бот", "urok7_hello_world_bot_improved.txt"),
    (2, 8): ("Работа с состояниями (FSM)", "urok8_sostoyaniya_fsm_improved.txt"),  # Переименован из 9
    (2, 9): ("Первая база данных (SQLite)", "urok9_baza_dannykh_sqlite_improved.txt"),  # Было 10
    (2, 10): ("Интеграция бота с GigaChat", "urok10_integratsiya_gigachat_improved.txt"),  # Было 11
    (2, 11): ("Настройка промптов для бота", "urok11_nastroyka_promptov_improved.txt"),  # Было 12
    (2, 12): ("Работа с документами", "urok12_rabota_s_dokumentami_improved.txt"),  # Было 13
    
    # МОДУЛЬ 3: Продвинутые возможности (4 урока)
    (3, 13): ("База знаний и RAG", "urok13_baza_znaniy_rag_improved.txt"),  # Было 14
    (3, 14): ("Гибридный поиск: FAISS + BM25", "urok14_gibridnyy_poisk_improved.txt"),  # Было 15
    (3, 15): ("Логирование и мониторинг", "urok15_logirovanie_improved.txt"),  # Было 16
    (3, 16): ("Оптимизация работы бота", "urok16_optimizatsiya_improved.txt"),  # Было 17
    
    # МОДУЛЬ 4: Production и деплой (4 урока)
    (4, 17): ("Подготовка к развёртыванию", "urok17_podgotovka_k_deployu_improved.txt"),  # Было 18
    (4, 18): ("Деплой бота на сервер", "urok18_deploy_na_server_improved.txt"),  # Было 19
    (4, 19): ("Обновление и поддержка", "urok19_obnovlenie_podderzhka_improved.txt"),  # Было 20
    (4, 20): ("Финальный проект – ваш бот", "urok20_finalnyy_proekt_improved.txt"),  # Было 21
}

def load_vibe_lessons(source_folder: str):
    """Загрузка уроков Vibe Coding в базу данных"""
    db = Database(config.DB_PATH)
    
    logging.info("🚀 Начало загрузки уроков Vibe Coding...")
    
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
            
            # Сохраняем в БД с course_id=2
            db.add_lesson_to_catalog(
                m_no=module_no,
                l_no=lesson_no,
                title=title,
                path=file_path,
                content=content,
                course_id=2  # ← Vibe Coding
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
    
    logging.info("База курса Vibe Coding готова!")

if __name__ == "__main__":
    # Путь к папке с улучшенными уроками
    SOURCE_FOLDER = "/mnt/user-data/outputs"
    
    # Альтернативно можно указать путь на Windows
    # SOURCE_FOLDER = r"C:\Users\BeltiugovRV\Desktop\Промтинг\outputs"
    
    load_vibe_lessons(SOURCE_FOLDER)
