import logging
from pathlib import Path
import yadisk

class YaDiskLoader:
    """Автоматическая загрузка файлов с публичной папки Яндекс.Диска"""
    
    def __init__(self, public_url: str, local_path: str):
        self.public_url = public_url
        self.local_path = Path(local_path)
        self.local_path.mkdir(parents=True, exist_ok=True)
        self.client = yadisk.Client()
    
    def download_all(self) -> bool:
        """Скачивание всех файлов из публичной папки"""
        try:
            logging.info(f"📥 Загрузка файлов с Яндекс.Диска...")
            public_key = self._extract_public_key(self.public_url)
            
            # Получаем список файлов
            files = list(self.client.public_listdir(public_key))
            
            if not files:
                logging.warning("⚠️ Папка пуста или недоступна")
                return False
            
            logging.info(f"📋 Найдено файлов: {len(files)}")
            
            downloaded = 0
            for item in files:
                try:
                    if item.type == 'file':
                        file_path = self.local_path / item.name
                        self.client.download_public(
                            public_key=public_key,
                            file_or_path=item.path,
                            path=str(file_path)
                        )
                        logging.info(f"✅ Загружен: {item.name}")
                        downloaded += 1
                except Exception as e:
                    logging.error(f"❌ Ошибка загрузки {item.name}: {e}")
            
            logging.info(f"✅ Загрузка завершена: {downloaded}/{len(files)} файлов")
            return downloaded > 0
            
        except Exception as e:
            logging.error(f"❌ Ошибка загрузки с Яндекс.Диска: {e}")
            return False
    
    def _extract_public_key(self, url: str) -> str:
        """Извлечение публичного ключа из URL"""
        if '/d/' in url:
            return url.split('/d/')[1].split('?')[0]
        return url
    
    def get_file_count(self) -> int:
        """Количество загруженных файлов"""
        if not self.local_path.exists():
            return 0
        return len(list(self.local_path.rglob('*.*')))