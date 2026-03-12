from gigachat import GigaChat
import asyncio
import logging
import time
import re
import json
from typing import Tuple, List, Dict, Optional
import config


class ClaudeService:
    """
    v16 — Сервис на официальной библиотеке GigaChat
    Решены все проблемы с SSL сертификатами
    """

    ABBREVIATIONS = {
        'еасуз': 'единая автоматизированная система управления закупками',
        'пик': 'портал исполнения контрактов',
        'электронный магазин': 'подсистема еасуз для закупок малого объема',
        'рхо': 'региональное хранилище объектов',
        'мгк': 'межведомственная контрольная комиссия',
        'окпд2': 'общероссийский классификатор продукции по видам экономической деятельности',
        'ктру': 'каталог товаров, работ, услуг',
        'нмцк': 'начальная (максимальная) цена контракта',
        'тз': 'техническое задание',
        'гк': 'государственный контракт',
        'фз-44': 'федеральный закон о контрактной системе в сфере закупок',
        'фз-223': 'федеральный закон о закупках отдельными видами юридических лиц'
    }

    _semaphore = asyncio.Semaphore(10)

    def __init__(self):
        if not config.GIGACHAT_AUTH_KEY:
            logging.error("❌ GIGACHAT_AUTH_KEY не найден в конфигурации!")
            raise ValueError("GIGACHAT_AUTH_KEY не установлен")
        
        # Инициализация GigaChat клиента
        self.client = GigaChat(
            credentials=config.GIGACHAT_AUTH_KEY,
            model=config.GIGACHAT_MODEL,
            verify_ssl_certs=False  # Отключаем проверку SSL
        )
        
        logging.info(f"[GigaChat] ✅ Инициализация: model={config.GIGACHAT_MODEL}, scope={config.GIGACHAT_SCOPE}")

    def _expand_abbreviations(self, text: str) -> str:
        expanded = text
        text_lower = text.lower()
        sorted_abbr = sorted(self.ABBREVIATIONS.items(), key=lambda x: len(x[0]), reverse=True)
        for abbr, full in sorted_abbr:
            pattern = r'\b' + re.escape(abbr) + r'\b'
            if re.search(pattern, text_lower):
                expanded = re.sub(pattern, full, expanded, flags=re.IGNORECASE)
        return expanded

    def sanitize_markdown(self, text: str) -> str:
        """Очистка и форматирование текста для Telegram"""
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('**', '*') 
        if len(text.encode('utf-8')) > 4096:
            text = text[:4000] + "\n\n... (текст сокращен)"
        return text.strip()

    async def generate_test(self, lesson_content: str) -> List[Dict]:
        """Генерация теста на основе содержания урока"""
        prompt = f"""Ты — ИИ-педагог. Изучи текст урока и создай мини-тест из 3 вопросов.
Текст урока: {lesson_content[:3000]}

Верни ответ ТОЛЬКО в формате JSON:
[
  {{"q": "Вопрос?", "options": ["Вариант1", "Вариант2", "Вариант3"], "correct": 0}},
  ...
]
(correct - это индекс правильного ответа от 0 до 2)"""
        
        async with self._semaphore:
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.chat(prompt)
                )
                
                content = response.choices[0].message.content
                match = re.search(r'\[.*\]', content, re.DOTALL)
                return json.loads(match.group()) if match else []
            except Exception as e:
                logging.error(f"[GigaChat] Ошибка generate_test: {e}")
                return []

    async def analyze_prompt(self, user_prompt: str) -> str:
        """Режим ТРЕНАЖЕР: анализ промпта по формуле РЦК-ФОТ"""
        prompt = f"""Ты — эксперт по промпт-инжинирингу. Проанализируй промпт пользователя по системе РЦК-ФОТ.

Промпт пользователя: "{user_prompt}"

ОБЯЗАТЕЛЬНАЯ СТРУКТУРА ОТВЕТА:

# Анализ промпта "{user_prompt[:50]}..." по системе РЦК-ФОТ

## 1. Что есть в промпте

[Перечисли, какие элементы РЦК-ФОТ присутствуют]

## 2. Чего не хватает

❌ Роль (Р): [Указано/Не указано, в какой роли должен выступать ИИ]
❌ Цель (Ц): [Размыта/Понятно, для чего нужен текст]
❌ Контекст (К): [Нет информации о целевой аудитории, назначении текста]
❌ Формат (Ф): [Не определён формат вывода]
❌ Ограничения (О): [Нет указаний по объёму, стилю, сложности]
❌ Тон (Т): [Не задан стиль текста]

## 3. Оценка: X/10

[Краткое пояснение оценки]

## 4. Идеальный вариант промпта

**ОБЯЗАТЕЛЬНО с разбивкой по РЦК-ФОТ:**

"Выступи в роли [роль]. Напиши [что именно]. Контекст: [для кого, зачем]. Формат: [структура]. Ограничения: [объём, стиль]. Тон: [стиль текста]."

**Или в виде списка:**
- Роль: [роль]
- Цель: [цель]
- Контекст: [контекст]
- Формат: [формат]
- Ограничения: [ограничения]
- Тон: [тон]

ВАЖНО: Раздел 4 "Идеальный вариант промпта" ОБЯЗАТЕЛЕН в каждом ответе!"""
        
        async with self._semaphore:
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.chat(prompt)
                )
                return response.choices[0].message.content
            except Exception as e:
                logging.error(f"[GigaChat] Ошибка analyze_prompt: {e}")
                return f"Ошибка тренажера: {str(e)}"

    async def ask(self, query: str, knowledge_base=None, category: str = None) -> Tuple[str, int]:
        """
        Основной метод поиска ответов (режим КОНСУЛЬТАНТ)
        """
        start_time = time.time()
        
        # 1. Расширяем сокращения
        expanded_query = self._expand_abbreviations(query)
        
        # 2. Ищем контекст в БД
        context = ""
        if knowledge_base:
            docs = knowledge_base.search_documents(expanded_query, limit=3)
            if docs:
                context = "\n\n".join([f"Источник ({d['title']}):\n{d['content']}" for d in docs])

        # 3. Формируем промпт с контекстом
        full_prompt = f"""Ты — эксперт-наставник по промпт-инжинирингу. 
Твоя задача: помогать пользователям писать эффективные промпты для работы с ИИ.
Используй предоставленный контекст из базы знаний, если он полезен.

КОНТЕКСТ:
{context}

ВОПРОС ПОЛЬЗОВАТЕЛЯ:
{query}
"""

        # 4. Запрос к GigaChat
        async with self._semaphore:
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.chat(full_prompt)
                )
                
                answer = self.sanitize_markdown(response.choices[0].message.content)
                duration_ms = int((time.time() - start_time) * 1000)
                logging.info(f"[GigaChat] ✅ Ответ получен: {duration_ms}ms")
                return answer, duration_ms
            except Exception as e:
                logging.error(f"[GigaChat] Network error: {e}")
                return "Ошибка сети. Проверьте соединение с GigaChat API.", 0