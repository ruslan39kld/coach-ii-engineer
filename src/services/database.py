import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict

class Database:
    """
    Класс для управления базой данных SQLite.
    Объединяет функции Базы Знаний (RAG) и Системы Обучения (LMS).
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logging.info(f"✅ База данных инициализирована: {db_path}")
    
    def _init_db(self):
        """Создание всех необходимых таблиц при запуске"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # --- 1. ТАБЛИЦЫ ДЛЯ КУРСА ОБУЧЕНИЯ ---
        
        # Прогресс ученика: на каком модуле, уроке и разделе остановился
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_learning_progress (
                user_id INTEGER PRIMARY KEY,
                current_module_no INTEGER DEFAULT 1,
                current_lesson_no INTEGER DEFAULT 1,
                current_section INTEGER DEFAULT 0,
                is_lesson_completed BOOLEAN DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Каталог уроков: хранит тексты, пути к файлам и вопросы тестов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lesson_catalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_no INTEGER,
                lesson_no INTEGER,
                title TEXT,
                file_path TEXT,
                content TEXT,
                test_data TEXT,
                course_id INTEGER DEFAULT 1
            )
        """)

        # Завершенные уроки (для отслеживания прогресса)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lesson_completions (
                user_id INTEGER,
                module_no INTEGER,
                lesson_no INTEGER,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                test_score INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, module_no, lesson_no)
            )
        """)

        # --- 2. ТАБЛИЦЫ БАЗЫ ЗНАНИЙ (ДЛЯ ПОИСКА) ---
        
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
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS faq (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                source_file TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # --- 3. ИСТОРИЯ И ЛОГИ ---
        
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
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query TEXT,
                answer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # --- 4. ТАБЛИЦА НЕЙРОСЕТЕЙ (НАВИГАТОР) ---
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                provider TEXT,
                region TEXT,
                access_info TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_queries_user_id ON queries(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_queries_created_at ON queries(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lesson_nav ON lesson_catalog(module_no, lesson_no)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_tools_category ON ai_tools(category)")
        
        # Добавляем колонку current_section если её нет (для старых БД)
        try:
            cursor.execute("ALTER TABLE user_learning_progress ADD COLUMN current_section INTEGER DEFAULT 0")
            logging.info("✅ Добавлена колонка current_section")
        except sqlite3.OperationalError:
            pass  # Колонка уже существует
        
        # НОВОЕ: Добавляем колонку course_id если её нет
        try:
            cursor.execute("ALTER TABLE lesson_catalog ADD COLUMN course_id INTEGER DEFAULT 1")
            logging.info("✅ Добавлена колонка course_id")
        except sqlite3.OperationalError:
            pass  # Колонка уже существует
        
        conn.commit()
        conn.close()

    # =========================================================================
    # МЕТОДЫ ДЛЯ СИСТЕМЫ ОБУЧЕНИЯ
    # =========================================================================

    def add_lesson_to_catalog(self, m_no: int, l_no: int, title: str, path: str, content: str, course_id: int = 1):
        """Добавляет или обновляет содержание урока в справочнике"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO lesson_catalog (module_no, lesson_no, title, file_path, content, course_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (m_no, l_no, title, path, content, course_id))
        conn.commit()
        conn.close()

    def get_user_progress(self, user_id: int) -> Tuple[int, int, int]:
        """Возвращает (модуль, урок, раздел) для пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT current_module_no, current_lesson_no, current_section 
            FROM user_learning_progress 
            WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row if row else (1, 1, 0)

    def update_user_progress(self, user_id: int, m_no: int, l_no: int, section: int = 0):
        """Сохраняет текущий шаг обучения (модуль, урок, раздел)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO user_learning_progress 
            (user_id, current_module_no, current_lesson_no, current_section, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, m_no, l_no, section))
        conn.commit()
        conn.close()

    def get_lesson(self, m_no: int, l_no: int):
        """Получает данные конкретного урока"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT title, content, test_data FROM lesson_catalog WHERE module_no = ? AND lesson_no = ?", (m_no, l_no))
        row = cursor.fetchone()
        conn.close()
        return row

    # =========================================================================
    # МЕТОДЫ ДЛЯ ОТСЛЕЖИВАНИЯ ЗАВЕРШЕННЫХ УРОКОВ
    # =========================================================================

    def mark_lesson_completed(self, user_id: int, m_no: int, l_no: int, test_score: int = 0):
        """Отмечает урок как завершенный"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO lesson_completions 
            (user_id, module_no, lesson_no, test_score, completed_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, m_no, l_no, test_score))
        conn.commit()
        conn.close()

    def get_completed_lessons(self, user_id: int) -> List[Tuple[int, int]]:
        """Возвращает список завершенных уроков [(module_no, lesson_no), ...]"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT module_no, lesson_no FROM lesson_completions
            WHERE user_id = ? ORDER BY module_no, lesson_no
        """, (user_id,))
        results = cursor.fetchall()
        conn.close()
        return results

    def get_all_lessons(self) -> List[Dict]:
        """Возвращает список всех уроков из каталога"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT module_no, lesson_no, title, course_id 
            FROM lesson_catalog 
            ORDER BY course_id, module_no, lesson_no
        """)
        lessons = []
        for row in cursor.fetchall():
            lessons.append({
                'module_no': row[0],
                'lesson_no': row[1],
                'title': row[2],
                'course_id': row[3] if len(row) > 3 else 1
            })
        conn.close()
        return lessons

    # =========================================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С БАЗОЙ ЗНАНИЙ
    # =========================================================================

    def load_document(self, filename: str, content: str, category: str = None, file_size: int = 0):
        """Сохраняет текст документа в поисковый индекс"""
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
        """Поиск по FAQ"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        words = query.lower().split()
        conditions = []
        params = []
        for word in words:
            if len(word) > 2:
                conditions.append("(LOWER(question) LIKE ? OR LOWER(answer) LIKE ?)")
                params.extend([f'%{word}%', f'%{word}%'])
        
        if not conditions:
            conn.close()
            return []
        
        sql = f"SELECT id, question, answer, source_file FROM faq WHERE {' OR '.join(conditions)} LIMIT ?"
        params.append(limit)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': r[0], 
            'title': r[1][:100], 
            'content': f"Q: {r[1]}\nA: {r[2]}", 
            'category': 'FAQ',
            'source_file': r[3]
        } for r in rows]

    def search_documents(self, query: str, limit: int = 5) -> list:
        """Универсальный поиск"""
        faq_results = self.search_faq(query, limit=limit)
        if faq_results:
            return faq_results
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        words = query.lower().split()
        conditions = []
        params = []
        for word in words:
            if len(word) > 2:
                conditions.append("(LOWER(content) LIKE ? OR LOWER(filename) LIKE ?)")
                params.extend([f'%{word}%', f'%{word}%'])
        
        if not conditions:
            conn.close()
            return []
            
        sql = f"SELECT id, filename, content, category FROM documents WHERE {' OR '.join(conditions)} LIMIT ?"
        params.append(limit)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [{'id': r[0], 'title': r[1], 'content': r[2], 'category': r[3]} for r in rows]

    # =========================================================================
    # МЕТОДЫ ДЛЯ НАВИГАТОРА
    # =========================================================================

    def add_ai_tool(self, category: str, name: str, description: str,
                    provider: str = None, region: str = None, access_info: str = None):
        """Добавляет нейросеть"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ai_tools (category, name, description, provider, region, access_info)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (category, name, description, provider, region, access_info))
        conn.commit()
        conn.close()

    def get_ai_tools_by_category(self, category: str) -> List[Dict]:
        """Получает нейросети по категории"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, category, name, description, provider, region, access_info 
            FROM ai_tools 
            WHERE category = ?
            ORDER BY region DESC, name
        """, (category,))
        tools = []
        for row in cursor.fetchall():
            tools.append({
                'id': row[0],
                'category': row[1],
                'name': row[2],
                'description': row[3],
                'provider': row[4],
                'region': row[5],
                'access_info': row[6]
            })
        conn.close()
        return tools

    def get_all_ai_tools(self) -> List[Dict]:
        """Получает все нейросети"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, category, name, description, provider, region, access_info 
            FROM ai_tools 
            ORDER BY category, region DESC, name
        """)
        tools = []
        for row in cursor.fetchall():
            tools.append({
                'id': row[0],
                'category': row[1],
                'name': row[2],
                'description': row[3],
                'provider': row[4],
                'region': row[5],
                'access_info': row[6]
            })
        conn.close()
        return tools

    # =========================================================================
    # ЛОГИРОВАНИЕ
    # =========================================================================

    def log_query(self, user_id: int, username: str, query: str, answer: str, response_time_ms: int = 0):
        """Записывает запрос в историю"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO queries (user_id, username, query, answer, response_time_ms)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, username or "", query, answer, response_time_ms))
        conn.commit()
        conn.close()

    def get_user_history(self, user_id: int, limit: int = 10) -> List[Tuple]:
        """История пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT query, answer, created_at FROM queries
            WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit))
        results = cursor.fetchall()
        conn.close()
        return results

    def get_stats(self) -> dict:
        """Статистика"""
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
    
    # =========================================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С КУРСАМИ
    # =========================================================================

    def get_course_name(self, course_id: int) -> str:
        """Получить название курса"""
        names = {
            1: "Промт-инженерия",
            2: "Vibe Coding",
            3: "Веб-приложения на ИИ"
        }
        return names.get(course_id, "Неизвестный курс")
    
    def get_user_course_progress(self, user_id: int, course_id: int) -> dict:
        """Получить прогресс пользователя по конкретному курсу"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Общее количество уроков в курсе
        cursor.execute(
            "SELECT COUNT(*) FROM lesson_catalog WHERE course_id = ?",
            (course_id,)
        )
        total_lessons = cursor.fetchone()[0]
        
        # Количество пройденных уроков
        cursor.execute("""
            SELECT COUNT(DISTINCT lc.lesson_no)
            FROM lesson_completions lc
            JOIN lesson_catalog cat ON lc.module_no = cat.module_no AND lc.lesson_no = cat.lesson_no
            WHERE lc.user_id = ? AND cat.course_id = ?
        """, (user_id, course_id))
        completed_lessons = cursor.fetchone()[0]
        
        # Процент прогресса
        progress_percentage = int((completed_lessons / total_lessons * 100)) if total_lessons > 0 else 0
        
        conn.close()
        
        return {
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'progress_percentage': progress_percentage
        }
