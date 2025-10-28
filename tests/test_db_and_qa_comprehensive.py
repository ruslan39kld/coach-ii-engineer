# -*- coding: utf-8 -*-
"""
Комплексный тест базы данных и системы вопрос-ответ
Проверяет:
1. Определение и подключение к базе данных
2. Структуру и содержимое таблиц
3. Функциональность поиска FAQ
4. Качество распознавания вопросов и ответов
"""
import sys
import os
import sqlite3
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import Database

class DatabaseQATest:
    """Класс для тестирования базы данных и системы Q&A"""
    
    def __init__(self, db_path="data/bot.db"):
        self.db_path = db_path
        self.db = None
        self.conn = None
        self.cursor = None
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'tests': []
        }
    
    def print_header(self, title):
        """Печать заголовка раздела"""
        print("\n" + "="*80)
        print(f"  {title}")
        print("="*80)
    
    def print_subheader(self, title):
        """Печать подзаголовка"""
        print(f"\n{'─'*80}")
        print(f"  {title}")
        print(f"{'─'*80}")
    
    def log_test(self, test_name, passed, message="", warning=False):
        """Логирование результата теста"""
        status = "✅ PASS" if passed else ("⚠️ WARN" if warning else "❌ FAIL")
        print(f"{status} | {test_name}")
        if message:
            print(f"        {message}")
        
        self.test_results['tests'].append({
            'name': test_name,
            'passed': passed,
            'warning': warning,
            'message': message
        })
        
        if passed:
            self.test_results['passed'] += 1
        elif warning:
            self.test_results['warnings'] += 1
        else:
            self.test_results['failed'] += 1
    
    def test_1_database_detection(self):
        """Тест 1: Определение базы данных"""
        self.print_header("ТЕСТ 1: ОПРЕДЕЛЕНИЕ БАЗЫ ДАННЫХ")
        
        # Проверка существования файла БД
        db_exists = os.path.exists(self.db_path)
        self.log_test(
            "Файл базы данных существует",
            db_exists,
            f"Путь: {self.db_path}"
        )
        
        if not db_exists:
            return False
        
        # Проверка размера БД
        db_size = os.path.getsize(self.db_path)
        size_mb = db_size / (1024 * 1024)
        self.log_test(
            "Размер базы данных",
            db_size > 0,
            f"Размер: {size_mb:.2f} MB"
        )
        
        # Подключение к БД
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            self.db = Database(self.db_path)
            self.log_test("Подключение к базе данных", True, "Успешно подключено")
            return True
        except Exception as e:
            self.log_test("Подключение к базе данных", False, f"Ошибка: {str(e)}")
            return False
    
    def test_2_database_structure(self):
        """Тест 2: Структура базы данных"""
        self.print_header("ТЕСТ 2: СТРУКТУРА БАЗЫ ДАННЫХ")
        
        # Получить список таблиц
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in self.cursor.fetchall()]
        
        print(f"\nНайдено таблиц: {len(tables)}")
        print(f"Таблицы: {', '.join(tables)}")
        
        # Проверка обязательных таблиц
        required_tables = ['faq', 'documents', 'queries', 'users']
        for table in required_tables:
            exists = table in tables
            self.log_test(
                f"Таблица '{table}' существует",
                exists
            )
            
            if exists:
                # Проверка структуры таблицы
                self.cursor.execute(f"PRAGMA table_info({table})")
                columns = self.cursor.fetchall()
                print(f"\n  Структура таблицы '{table}':")
                for col in columns:
                    print(f"    - {col[1]} ({col[2]})")
                
                # Подсчет записей
                self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = self.cursor.fetchone()[0]
                print(f"  Записей: {count}")
        
        return len([t for t in required_tables if t in tables]) == len(required_tables)
    
    def test_3_faq_content(self):
        """Тест 3: Содержимое FAQ таблицы"""
        self.print_header("ТЕСТ 3: СОДЕРЖИМОЕ FAQ ТАБЛИЦЫ")
        
        # Общее количество FAQ
        self.cursor.execute("SELECT COUNT(*) FROM faq")
        faq_count = self.cursor.fetchone()[0]
        
        self.log_test(
            "FAQ таблица содержит данные",
            faq_count > 0,
            f"Всего записей: {faq_count}"
        )
        
        if faq_count == 0:
            return False
        
        # Проверка качества данных
        self.cursor.execute("SELECT COUNT(*) FROM faq WHERE question IS NULL OR question = ''")
        empty_questions = self.cursor.fetchone()[0]
        self.log_test(
            "Все вопросы заполнены",
            empty_questions == 0,
            f"Пустых вопросов: {empty_questions}" if empty_questions > 0 else "Все вопросы заполнены"
        )
        
        self.cursor.execute("SELECT COUNT(*) FROM faq WHERE answer IS NULL OR answer = ''")
        empty_answers = self.cursor.fetchone()[0]
        self.log_test(
            "Все ответы заполнены",
            empty_answers == 0,
            f"Пустых ответов: {empty_answers}" if empty_answers > 0 else "Все ответы заполнены"
        )
        
        # Источники FAQ
        self.cursor.execute("SELECT DISTINCT source_file FROM faq")
        sources = [row[0] for row in self.cursor.fetchall()]
        print(f"\n  Источников FAQ: {len(sources)}")
        
        # Топ-5 источников
        self.cursor.execute("""
            SELECT source_file, COUNT(*) as cnt 
            FROM faq 
            GROUP BY source_file 
            ORDER BY cnt DESC 
            LIMIT 5
        """)
        print("\n  Топ-5 источников по количеству вопросов:")
        for source, count in self.cursor.fetchall():
            print(f"    - {source}: {count} вопросов")
        
        # Примеры FAQ
        self.cursor.execute("SELECT question, answer, source_file FROM faq LIMIT 3")
        print("\n  Примеры FAQ записей:")
        for i, (q, a, src) in enumerate(self.cursor.fetchall(), 1):
            print(f"\n  {i}. Вопрос: {q[:70]}...")
            print(f"     Ответ: {a[:70]}...")
            print(f"     Источник: {src}")
        
        return True
    
    def test_4_search_functionality(self):
        """Тест 4: Функциональность поиска"""
        self.print_header("ТЕСТ 4: ФУНКЦИОНАЛЬНОСТЬ ПОИСКА FAQ")
        
        # Тестовые запросы с ожидаемыми результатами
        test_queries = [
            {
                'query': 'регистрация в ЕАСУЗ',
                'min_results': 1,
                'description': 'Поиск по регистрации'
            },
            {
                'query': 'план-график закупок',
                'min_results': 1,
                'description': 'Поиск по плану-графику'
            },
            {
                'query': 'контракт единственный поставщик',
                'min_results': 1,
                'description': 'Поиск по контрактам'
            },
            {
                'query': 'СМСП малый бизнес',
                'min_results': 1,
                'description': 'Поиск по СМСП'
            },
            {
                'query': 'экономия бюджет',
                'min_results': 1,
                'description': 'Поиск по экономии'
            }
        ]
        
        print("\n  Тестирование поисковых запросов:\n")
        
        total_passed = 0
        for test in test_queries:
            query = test['query']
            min_results = test['min_results']
            description = test['description']
            
            try:
                results = self.db.search_faq(query, limit=5)
                found = len(results)
                passed = found >= min_results
                
                self.log_test(
                    description,
                    passed,
                    f"Запрос: '{query}' | Найдено: {found} результатов"
                )
                
                if passed and results:
                    print(f"        Топ результат: {results[0]['title'][:60]}...")
                    total_passed += 1
                    
            except Exception as e:
                self.log_test(
                    description,
                    False,
                    f"Ошибка поиска: {str(e)}"
                )
        
        # Общий результат поиска
        search_quality = (total_passed / len(test_queries)) * 100
        self.log_test(
            "Общее качество поиска",
            search_quality >= 60,
            f"Успешных запросов: {total_passed}/{len(test_queries)} ({search_quality:.1f}%)",
            warning=(search_quality >= 40 and search_quality < 60)
        )
        
        return search_quality >= 40
    
    def test_5_qa_recognition(self):
        """Тест 5: Распознавание вопрос-ответ"""
        self.print_header("ТЕСТ 5: КАЧЕСТВО РАСПОЗНАВАНИЯ ВОПРОС-ОТВЕТ")
        
        # Проверка качества вопросов
        self.cursor.execute("""
            SELECT AVG(LENGTH(question)) as avg_q_len,
                   MIN(LENGTH(question)) as min_q_len,
                   MAX(LENGTH(question)) as max_q_len
            FROM faq
        """)
        avg_q, min_q, max_q = self.cursor.fetchone()
        
        print(f"\n  Статистика вопросов:")
        print(f"    - Средняя длина: {avg_q:.0f} символов")
        print(f"    - Минимальная: {min_q} символов")
        print(f"    - Максимальная: {max_q} символов")
        
        self.log_test(
            "Вопросы имеют адекватную длину",
            avg_q > 10 and avg_q < 500,
            f"Средняя длина: {avg_q:.0f} символов"
        )
        
        # Проверка качества ответов
        self.cursor.execute("""
            SELECT AVG(LENGTH(answer)) as avg_a_len,
                   MIN(LENGTH(answer)) as min_a_len,
                   MAX(LENGTH(answer)) as max_a_len
            FROM faq
        """)
        avg_a, min_a, max_a = self.cursor.fetchone()
        
        print(f"\n  Статистика ответов:")
        print(f"    - Средняя длина: {avg_a:.0f} символов")
        print(f"    - Минимальная: {min_a} символов")
        print(f"    - Максимальная: {max_a} символов")
        
        self.log_test(
            "Ответы имеют адекватную длину",
            avg_a > 20 and avg_a < 5000,
            f"Средняя длина: {avg_a:.0f} символов"
        )
        
        # Проверка соотношения длины вопросов и ответов
        ratio = avg_a / avg_q if avg_q > 0 else 0
        self.log_test(
            "Соотношение длины ответов к вопросам",
            ratio > 1 and ratio < 50,
            f"Соотношение: {ratio:.1f}:1",
            warning=(ratio >= 0.5 and ratio <= 1) or (ratio >= 50 and ratio < 100)
        )
        
        # Проверка разнообразия вопросов
        self.cursor.execute("SELECT COUNT(DISTINCT question) FROM faq")
        unique_questions = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM faq")
        total_questions = self.cursor.fetchone()[0]
        
        uniqueness = (unique_questions / total_questions * 100) if total_questions > 0 else 0
        self.log_test(
            "Уникальность вопросов",
            uniqueness > 90,
            f"Уникальных: {unique_questions}/{total_questions} ({uniqueness:.1f}%)",
            warning=(uniqueness >= 70 and uniqueness <= 90)
        )
        
        return True
    
    def test_6_database_stats(self):
        """Тест 6: Общая статистика базы данных"""
        self.print_header("ТЕСТ 6: ОБЩАЯ СТАТИСТИКА БАЗЫ ДАННЫХ")
        
        stats = self.db.get_stats()
        
        print(f"\n  📊 Статистика базы данных:")
        print(f"    📚 FAQ вопросов:        {stats['faq']}")
        print(f"    📄 Документов:          {stats['documents']}")
        print(f"    📝 Запросов:            {stats['queries']}")
        print(f"    👥 Пользователей:       {stats['users']}")
        
        # Проверка минимальных требований
        self.log_test(
            "Достаточно FAQ записей",
            stats['faq'] >= 100,
            f"FAQ записей: {stats['faq']}",
            warning=(stats['faq'] >= 50 and stats['faq'] < 100)
        )
        
        self.log_test(
            "Документы загружены",
            stats['documents'] > 0,
            f"Документов: {stats['documents']}",
            warning=True if stats['documents'] == 0 else False
        )
        
        return stats['faq'] > 0
    
    def print_summary(self):
        """Печать итоговой сводки"""
        self.print_header("ИТОГОВАЯ СВОДКА ТЕСТИРОВАНИЯ")
        
        total = self.test_results['passed'] + self.test_results['failed'] + self.test_results['warnings']
        passed_percent = (self.test_results['passed'] / total * 100) if total > 0 else 0
        
        print(f"""
  Всего тестов:      {total}
  ✅ Пройдено:       {self.test_results['passed']} ({passed_percent:.1f}%)
  ❌ Провалено:      {self.test_results['failed']}
  ⚠️  Предупреждения: {self.test_results['warnings']}
""")
        
        if self.test_results['failed'] > 0:
            print("  Проваленные тесты:")
            for test in self.test_results['tests']:
                if not test['passed'] and not test['warning']:
                    print(f"    ❌ {test['name']}")
                    if test['message']:
                        print(f"       {test['message']}")
        
        if self.test_results['warnings'] > 0:
            print("\n  Предупреждения:")
            for test in self.test_results['tests']:
                if test['warning']:
                    print(f"    ⚠️  {test['name']}")
                    if test['message']:
                        print(f"       {test['message']}")
        
        print("\n" + "="*80)
        if self.test_results['failed'] == 0:
            print("  ✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        elif passed_percent >= 70:
            print("  ⚠️  ТЕСТЫ ПРОЙДЕНЫ С ПРЕДУПРЕЖДЕНИЯМИ")
        else:
            print("  ❌ ТЕСТИРОВАНИЕ НЕ ПРОЙДЕНО")
        print("="*80)
        
        # Сохранение результатов
        self.save_results()
    
    def save_results(self):
        """Сохранение результатов в файл"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open('tests/TEST_DB_QA_RESULTS.md', 'w', encoding='utf-8') as f:
            f.write(f"# Результаты тестирования базы данных и Q&A\n\n")
            f.write(f"**Дата:** {timestamp}\n\n")
            
            f.write("## Сводка\n\n")
            total = self.test_results['passed'] + self.test_results['failed'] + self.test_results['warnings']
            passed_percent = (self.test_results['passed'] / total * 100) if total > 0 else 0
            
            f.write(f"- Всего тестов: {total}\n")
            f.write(f"- ✅ Пройдено: {self.test_results['passed']} ({passed_percent:.1f}%)\n")
            f.write(f"- ❌ Провалено: {self.test_results['failed']}\n")
            f.write(f"- ⚠️ Предупреждения: {self.test_results['warnings']}\n\n")
            
            f.write("## Детальные результаты\n\n")
            for test in self.test_results['tests']:
                status = "✅" if test['passed'] else ("⚠️" if test['warning'] else "❌")
                f.write(f"### {status} {test['name']}\n\n")
                if test['message']:
                    f.write(f"{test['message']}\n\n")
        
        print(f"\n  💾 Результаты сохранены в: tests/TEST_DB_QA_RESULTS.md")
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("\n")
        print("╔" + "="*78 + "╗")
        print("║" + " "*20 + "КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ БАЗЫ ДАННЫХ" + " "*22 + "║")
        print("║" + " "*25 + "И СИСТЕМЫ ВОПРОС-ОТВЕТ" + " "*32 + "║")
        print("╚" + "="*78 + "╝")
        
        try:
            # Запуск тестов
            if not self.test_1_database_detection():
                print("\n❌ Критическая ошибка: База данных не найдена!")
                return False
            
            self.test_2_database_structure()
            self.test_3_faq_content()
            self.test_4_search_functionality()
            self.test_5_qa_recognition()
            self.test_6_database_stats()
            
            # Итоговая сводка
            self.print_summary()
            
            return self.test_results['failed'] == 0
            
        except Exception as e:
            print(f"\n❌ Критическая ошибка при тестировании: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            if self.conn:
                self.conn.close()


def main():
    """Главная функция"""
    tester = DatabaseQATest()
    success = tester.run_all_tests()
    
    # Возврат кода выхода
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
