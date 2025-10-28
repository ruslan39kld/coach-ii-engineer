"""
Главный файл запуска EASUZ бота
"""
import sys
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / 'src'))

if __name__ == "__main__":
    # Импортируем и запускаем
    from bot import main
    main()