"""
Менеджер базы данных для бота ИИ Инженер
Отслеживание прогресса пользователей по курсам
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os


class DatabaseManager:
    """Управление базой данных бота"""
    
    def __init__(self, db_path: str = "data/progress.db"):
        self.db_path = db_path
        self._ensure_data_directory()
        self.init_database()
    
    def _ensure_data_directory(self):
        """Создает директорию data, если её нет"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_connection(self):
        """Создает подключение к базе данных"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Инициализация структуры базы данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_activity DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Таблица курсов
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT UNIQUE NOT NULL,
            course_slug TEXT UNIQUE NOT NULL,
            total_lessons INTEGER NOT NULL,
            description TEXT,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Таблица прогресса по урокам
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS lesson_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            lesson_number INTEGER NOT NULL,
            completed BOOLEAN DEFAULT 0,
            completion_date DATETIME,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (course_id) REFERENCES courses(course_id),
            UNIQUE(user_id, course_id, lesson_number)
        )
        """)
        
        # Таблица начала обучения (для отчета)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS course_enrollment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (course_id) REFERENCES courses(course_id),
            UNIQUE(user_id, course_id)
        )
        """)
        
        # Логирование активности
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            action_data TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """)
        
        conn.commit()
        conn.close()
        
        # Инициализация курсов
        self._init_default_courses()
    
    def _init_default_courses(self):
        """Добавляет курсы по умолчанию"""
        courses = [
            {
                'course_name': 'Промт-инженерия',
                'course_slug': 'prompt_engineering',
                'total_lessons': 23,
                'description': 'Полный курс по промт-инженерии: от основ до продвинутых техник'
            },
            {
                'course_name': 'Vibe Coding',
                'course_slug': 'vibe_coding',
                'total_lessons': 20,
                'description': 'Методология разработки с использованием ИИ: 20 практических уроков'
            },
            {
                'course_name': 'Веб-приложения на ИИ',
                'course_slug': 'web_ai',
                'total_lessons': 18,
                'description': 'Создание AI веб-приложений с Google AI Studio: 5 модулей, 18 уроков'
            }
        ]
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for course in courses:
            cursor.execute("""
                INSERT OR IGNORE INTO courses (course_name, course_slug, total_lessons, description)
                VALUES (?, ?, ?, ?)
            """, (course['course_name'], course['course_slug'], course['total_lessons'], course['description']))
        
        conn.commit()
        conn.close()
    
    # === ПОЛЬЗОВАТЕЛИ ===
    
    def register_user(self, user_id: int, username: str = None, 
                     first_name: str = None, last_name: str = None):
        """Регистрация нового пользователя или обновление данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, registration_date, last_activity)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                last_activity = excluded.last_activity
        """, (user_id, username, first_name, last_name, datetime.now(), datetime.now()))
        
        conn.commit()
        conn.close()
    
    def update_user_activity(self, user_id: int):
        """Обновление времени последней активности"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users SET last_activity = ? WHERE user_id = ?
        """, (datetime.now(), user_id))
        
        conn.commit()
        conn.close()
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получение данных пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, username, first_name, last_name, registration_date, last_activity
            FROM users WHERE user_id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'last_name': row[3],
                'registration_date': row[4],
                'last_activity': row[5]
            }
        return None
    
    # === КУРСЫ ===
    
    def get_course_by_slug(self, slug: str) -> Optional[Dict]:
        """Получение курса по slug"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT course_id, course_name, course_slug, total_lessons, description
            FROM courses WHERE course_slug = ?
        """, (slug,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'course_id': row[0],
                'course_name': row[1],
                'course_slug': row[2],
                'total_lessons': row[3],
                'description': row[4]
            }
        return None
    
    def get_all_courses(self) -> List[Dict]:
        """Получение всех курсов"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT course_id, course_name, course_slug, total_lessons, description
            FROM courses ORDER BY course_id
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'course_id': row[0],
            'course_name': row[1],
            'course_slug': row[2],
            'total_lessons': row[3],
            'description': row[4]
        } for row in rows]
    
    # === ЗАПИСЬ НА КУРС ===
    
    def enroll_user(self, user_id: int, course_slug: str):
        """Записывает пользователя на курс (фиксирует дату начала)"""
        course = self.get_course_by_slug(course_slug)
        if not course:
            return False
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR IGNORE INTO course_enrollment (user_id, course_id, start_date)
            VALUES (?, ?, ?)
        """, (user_id, course['course_id'], datetime.now()))
        
        conn.commit()
        conn.close()
        return True
    
    def get_enrollment_date(self, user_id: int, course_slug: str) -> Optional[datetime]:
        """Получение даты начала обучения на курсе"""
        course = self.get_course_by_slug(course_slug)
        if not course:
            return None
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT start_date FROM course_enrollment
            WHERE user_id = ? AND course_id = ?
        """, (user_id, course['course_id']))
        
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else None
    
    # === ПРОГРЕСС ПО УРОКАМ ===
    
    def mark_lesson_completed(self, user_id: int, course_slug: str, lesson_number: int):
        """Отмечает урок как завершенный"""
        course = self.get_course_by_slug(course_slug)
        if not course:
            return False
        
        # Автоматически записываем на курс, если еще не записан
        self.enroll_user(user_id, course_slug)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO lesson_progress (user_id, course_id, lesson_number, completed, completion_date)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(user_id, course_id, lesson_number) DO UPDATE SET
                completed = 1,
                completion_date = excluded.completion_date
        """, (user_id, course['course_id'], lesson_number, datetime.now()))
        
        conn.commit()
        conn.close()
        
        # Логируем активность
        self.log_activity(user_id, 'lesson_completed', 
                         f'{course_slug}:lesson_{lesson_number}')
        
        return True
    
    def get_user_progress(self, user_id: int, course_slug: str) -> Dict:
        """Получение прогресса пользователя по курсу"""
        course = self.get_course_by_slug(course_slug)
        if not course:
            return {'completed': 0, 'total': 0, 'percentage': 0, 'lessons': []}
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT lesson_number, completed, completion_date
            FROM lesson_progress
            WHERE user_id = ? AND course_id = ?
            ORDER BY lesson_number
        """, (user_id, course['course_id']))
        
        rows = cursor.fetchall()
        conn.close()
        
        lessons = [{
            'lesson_number': row[0],
            'completed': bool(row[1]),
            'completion_date': row[2]
        } for row in rows]
        
        completed = sum(1 for l in lessons if l['completed'])
        total = course['total_lessons']
        percentage = (completed / total * 100) if total > 0 else 0
        
        return {
            'completed': completed,
            'total': total,
            'percentage': round(percentage, 1),
            'lessons': lessons,
            'is_finished': completed == total
        }
    
    def get_all_user_progress(self, user_id: int) -> Dict[str, Dict]:
        """Получение прогресса пользователя по всем курсам"""
        courses = self.get_all_courses()
        progress = {}
        
        for course in courses:
            progress[course['course_slug']] = self.get_user_progress(user_id, course['course_slug'])
        
        return progress
    
    # === ЛОГИРОВАНИЕ ===
    
    def log_activity(self, user_id: int, action_type: str, action_data: str = None):
        """Логирование действий пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO activity_log (user_id, action_type, action_data, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_id, action_type, action_data, datetime.now()))
        
        conn.commit()
        conn.close()
        
        # Обновляем last_activity
        self.update_user_activity(user_id)
    
    # === СТАТИСТИКА ДЛЯ АДМИНКИ ===
    
    def get_total_users(self) -> int:
        """Общее количество пользователей"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    
    def get_course_statistics(self, course_slug: str) -> Dict:
        """Статистика по курсу"""
        course = self.get_course_by_slug(course_slug)
        if not course:
            return {}
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Всего записано
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) FROM course_enrollment
            WHERE course_id = ?
        """, (course['course_id'],))
        enrolled = cursor.fetchone()[0]
        
        # Завершили курс (все уроки пройдены)
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) FROM (
                SELECT user_id, COUNT(*) as completed_count
                FROM lesson_progress
                WHERE course_id = ? AND completed = 1
                GROUP BY user_id
                HAVING completed_count = ?
            )
        """, (course['course_id'], course['total_lessons']))
        completed = cursor.fetchone()[0]
        
        conn.close()
        
        completion_rate = (completed / enrolled * 100) if enrolled > 0 else 0
        
        return {
            'course_name': course['course_name'],
            'enrolled': enrolled,
            'completed': completed,
            'in_progress': enrolled - completed,
            'completion_rate': round(completion_rate, 1)
        }
    
    def get_all_users_for_report(self) -> List[Dict]:
        """Получение всех пользователей с их прогрессом для Excel-отчета"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                u.user_id,
                u.username,
                u.first_name,
                u.last_name,
                u.registration_date
            FROM users u
            ORDER BY u.registration_date DESC
        """)
        
        users = cursor.fetchall()
        conn.close()
        
        report_data = []
        
        for user in users:
            user_id = user[0]
            username = user[1] or ''
            first_name = user[2] or ''
            last_name = user[3] or ''
            registration_date = user[4]
            
            # Полное имя
            full_name = f"{first_name} {last_name}".strip() or username or f"User_{user_id}"
            
            # Прогресс по курсам
            courses = self.get_all_courses()
            course_progress = {}
            
            for course in courses:
                progress = self.get_user_progress(user_id, course['course_slug'])
                enrollment_date = self.get_enrollment_date(user_id, course['course_slug'])
                
                course_progress[course['course_slug']] = {
                    'completed': progress['completed'],
                    'total': progress['total'],
                    'is_finished': progress['is_finished'],
                    'enrollment_date': enrollment_date
                }
            
            report_data.append({
                'user_id': user_id,
                'full_name': full_name,
                'registration_date': registration_date,
                'courses': course_progress
            })
        
        return report_data


# Глобальный экземпляр
db = DatabaseManager()
