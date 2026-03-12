import os
import re
import sys
import logging

# Добавляем папку src в путь импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.database import Database
import config

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Путь к базе курса
BASE_PATH = r"C:\Users\BeltiugovRV\Desktop\AI Инженер\БАЗА\Промт-инженер"

def load_lessons():
    """Загрузка всех уроков в базу данных"""
    db = Database(config.DB_PATH)
    
    logging.info("🚀 Начало индексации курса...")
    
    # Сканируем модули
    modules = sorted([d for d in os.listdir(BASE_PATH) if d.startswith("Модуль")])
    
    total_lessons = 0
    
    for module_folder in modules:
        # Извлекаем номер модуля
        match = re.search(r'Модуль (\d+)', module_folder)
        if not match:
            continue
        module_no = int(match.group(1))
        
        module_path = os.path.join(BASE_PATH, module_folder)
        
        # Сканируем уроки внутри модуля
        lessons = sorted([d for d in os.listdir(module_path) if d.startswith("Урок")])
        
        for lesson_folder in lessons:
            # Извлекаем номер урока
            match = re.search(r'Урок (\d+)', lesson_folder)
            if not match:
                continue
            lesson_no = int(match.group(1))
            
            lesson_path = os.path.join(module_path, lesson_folder)
            
            # Ищем файл urokX_structured.txt
            structured_file = f"urok{lesson_no}_structured.txt"
            file_path = os.path.join(lesson_path, structured_file)
            
            if not os.path.exists(file_path):
                logging.warning(f"⚠️ Файл не найден: {file_path}")
                continue
            
            # Читаем содержимое
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Извлекаем заголовок из первой строки или из названия папки
                title_match = re.search(r'УРОК \d+[:.]\s*(.+)', content)
                if title_match:
                    title = title_match.group(1).strip()
                else:
                    # Берем из названия папки
                    title = lesson_folder.replace(f"Урок {lesson_no}. ", "")
                
                # Сохраняем в БД
                db.add_lesson_to_catalog(module_no, lesson_no, title, file_path, content)
                
                logging.info(f"✅ Модуль {module_no} | Урок {lesson_no}: {title}")
                total_lessons += 1
                
            except Exception as e:
                logging.error(f"❌ Ошибка при обработке {file_path}: {e}")
    
    logging.info(f"\n✨ Загружено уроков: {total_lessons}")
    logging.info("База курса готова!")

if __name__ == "__main__":
    load_lessons()