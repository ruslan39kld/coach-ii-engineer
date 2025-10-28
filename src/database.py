import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

class Database:
    """SQLite база данных для хранения логов и истории"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logging.info(f"✅ База данных инициализирована: {db_path}")
    
    def _init_db(self):
        """Создание таблиц"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица документов (индекс базы знаний)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                content TEXT,
                category TEXT,
                file_size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица запросов пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                query TEXT NOT NULL,
                answer TEXT,
                response_time_ms INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица избранного
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query TEXT,
                answer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Индексы для оптимизации
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_queries_user_id ON queries(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_queries_created_at ON queries(created_at)")
        
        conn.commit()
        conn.close()
    
    def load_document(self, filename: str, content: str, category: str = None, file_size: int = 0):
        """Загрузка документа в индекс"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO documents 
                (filename, content, category, file_size, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (filename, content, category, file_size, datetime.now()))
            conn.commit()
        except Exception as e:
            logging.error(f"Ошибка загрузки документа {filename}: {e}")
        finally:
            conn.close()
    
    def search_faq(self, query: str, limit: int = 5) -> list:
        """
        Поиск в FAQ базе
        
        Args:
            query: поисковый запрос
            limit: максимальное количество результатов
        
        Returns:
            list: список словарей с найденными вопросами-ответами
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Разбиваем запрос на слова для лучшего поиска
        words = query.lower().split()
        
        # Строим запрос с OR для каждого слова
        conditions = []
        params = []
        for word in words:
            if len(word) > 2:  # Игнорируем короткие слова
                conditions.append("(LOWER(question) LIKE ? OR LOWER(answer) LIKE ?)")
                params.extend([f'%{word}%', f'%{word}%'])
        
        if not conditions:
            conn.close()
            return []
        
        sql = f"""
            SELECT id, question, answer, source_file 
            FROM faq 
            WHERE {' OR '.join(conditions)}
            LIMIT ?
        """
        params.append(limit)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Преобразуем кортежи в словари
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'title': row[1][:100] + '...' if len(row[1]) > 100 else row[1],  # вопрос как title
                'content': f"Вопрос: {row[1]}\n\nОтвет: {row[2]}",
                'category': 'FAQ',
                'source_file': row[3]
            })
        
        logging.info(f"[Database] Найдено FAQ: {len(results)}")
        if results:
            logging.info(f"[Database] Первый FAQ: {results[0]['title'][:50]}")
        
        return results
    
    def search_documents(self, query: str, limit: int = 5) -> list:
        """
        Поиск документов по запросу (сначала в FAQ, потом в documents)
        
        Args:
            query: поисковый запрос
            limit: максимальное количество результатов
        
        Returns:
            list: список словарей с найденными документами
        """
        # Сначала ищем в FAQ
        faq_results = self.search_faq(query, limit=limit)
        
        if faq_results:
            logging.info(f"[Database] Используем FAQ результаты: {len(faq_results)}")
            return faq_results
        
        # Если в FAQ ничего не найдено, ищем в documents
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Разбиваем запрос на слова для лучшего поиска
        words = query.lower().split()
        
        # Строим запрос с OR для каждого слова
        conditions = []
        params = []
        for word in words:
            if len(word) > 2:  # Игнорируем короткие слова
                conditions.append("(LOWER(content) LIKE ? OR LOWER(filename) LIKE ?)")
                params.extend([f'%{word}%', f'%{word}%'])
        
        if not conditions:
            conn.close()
            return []
        
        sql = f"""
            SELECT id, filename, content, category 
            FROM documents 
            WHERE {' OR '.join(conditions)}
            LIMIT ?
        """
        params.append(limit)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        # ВАЖНО: Преобразуем кортежи в словари
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'title': row[1],  # используем filename как title
                'content': row[2],
                'category': row[3]
            })
        
        logging.info(f"[Database] Найдено документов: {len(results)}")
        if results:
            logging.info(f"[Database] Первый документ: {results[0]['title'][:50]}")
        
        return results
    
    def log_query(self, user_id: int, username: str, query: str, answer: str, response_time_ms: int = 0):
        """Логирование запроса пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO queries 
            (user_id, username, query, answer, response_time_ms)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, username or "", query, answer, response_time_ms))
        
        conn.commit()
        conn.close()
    
    def get_user_history(self, user_id: int, limit: int = 10) -> List[Tuple]:
        """Получение истории запросов пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT query, answer, created_at
            FROM queries
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_stats(self) -> dict:
        """Получение статистики базы"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM documents")
        docs_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM faq")
        faq_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM queries")
        queries_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM queries")
        users_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'documents': docs_count,
            'faq': faq_count,
            'queries': queries_count,
            'users': users_count
        }


class KnowledgeBase:
    """Загрузка и индексация документов"""
    
    def __init__(self, kb_path: str, database: Database):
        self.kb_path = Path(kb_path)
        self.db = database
    
    def load_all_files(self):
        """Загрузка всех файлов в базу данных"""
        if not self.kb_path.exists():
            logging.warning(f"⚠️ Папка {self.kb_path} не существует")
            return
        
        files = list(self.kb_path.rglob('*.*'))
        pdf_files = [f for f in files if f.suffix.lower() in ['.pdf', '.docx', '.txt', '.doc']]
        
        logging.info(f"📚 Найдено файлов для индексации: {len(pdf_files)}")
        
        for file in pdf_files:
            try:
                content = self._read_file(file)
                if content:
                    self.db.load_document(
                        filename=file.name,
                        content=content,
                        category=self._detect_category(file.name),
                        file_size=file.stat().st_size
                    )
                    logging.info(f"✅ Проиндексирован: {file.name}")
            except Exception as e:
                logging.error(f"❌ Ошибка чтения {file.name}: {e}")
        
        logging.info("✅ Индексация завершена")
    
    def _read_file(self, filepath: Path) -> str:
        """Чтение содержимого файла"""
        try:
            if filepath.suffix.lower() == '.txt':
                return filepath.read_text(encoding='utf-8', errors='ignore')
            
            elif filepath.suffix.lower() == '.docx':
                from docx import Document
                doc = Document(filepath)
                return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            
            elif filepath.suffix.lower() == '.pdf':
                from PyPDF2 import PdfReader
                reader = PdfReader(filepath)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logging.error(f"Ошибка чтения {filepath.name}: {e}")
        return ""
    
    def _detect_category(self, filename: str) -> str:
        """Определение категории по имени файла"""
        filename_lower = filename.lower()
        
        categories = {
            'План-график': ['план', 'график', 'пг'],
            'Проведение закупок': ['закупк', 'аукцион', 'конкурс', 'котировк'],
            'Документы': ['документ', 'блок', 'форма', 'заполн'],
            'Технические': ['рхо', 'ктру', 'техн', 'система'],
            'Регламенты': ['регламент', 'инструкц', 'порядок'],
        }
        
        for category, keywords in categories.items():
            if any(kw in filename_lower for kw in keywords):
                return category
        return 'Общие'