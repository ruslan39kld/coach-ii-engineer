import httpx
import asyncio
import logging
import time
import re
from typing import Tuple
import config
from prompts import SYSTEM_PROMPT
from hybrid_search import HybridSearch

class ClaudeService:
    """Сервис для работы с Claude AI через vsegpt.ru (ASYNC с httpx)"""
    
    def __init__(self):
        self.api_key = config.CLAUDE_API_KEY
        self.endpoint = config.CLAUDE_ENDPOINT
        self.model = config.CLAUDE_MODEL
        self.hybrid_search = HybridSearch()
        
        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY не установлен")
    
    def _extract_keywords(self, text: str) -> list:
        """Извлечь ключевые слова из текста"""
        stop_words = {'как', 'что', 'где', 'когда', 'для', 'или', 'и', 'в', 'на', 'с', 'по', 'я', 'мне', 'нужно', 'можно', 'это', 'быть'}
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        return keywords[:5]
    
    async def ask(self, query: str, database) -> Tuple[str, int]:
        """Отправка запроса в Claude AI с умным поиском (ASYNC)"""
        start_time = time.time()
        
        logging.info(f"[ClaudeService] Начало обработки запроса: {query[:50]}...")
        
        # Извлекаем ключевые слова для улучшенного поиска
        keywords = self._extract_keywords(query)
        search_query = " ".join(keywords) if keywords else query
        
        logging.info(f"[ClaudeService] Ключевые слова: {keywords}")
        logging.info(f"[ClaudeService] Поисковый запрос: '{search_query}'")
        
        # Поиск документов гибридным поиском (FAISS + BM25)
        docs = self.hybrid_search.search(search_query, top_k=3, vector_weight=0.7)
        
        logging.info(f"[ClaudeService] Найдено документов: {len(docs)}")
        
        if not docs:
            logging.warning("[ClaudeService] Документы не найдены")
            return self._no_docs_response(), int((time.time() - start_time) * 1000)
        
        # Логируем найденные документы
        for i, doc in enumerate(docs[:3], 1):
            logging.info(f"  {i}. {doc.get('question','')[:60]} | score={doc.get('score',0):.3f}")
        
        # Формирование контекста из найденных документов
        context = self._build_context(docs)
        full_prompt = self._build_full_prompt(query, context)
        
        # Детальное логирование перед отправкой
        logging.info(f"[Claude] Отправляем контекст из {len(docs)} документов")
        logging.info(f"[Claude] Первый документ: {docs[0].get('question','')[:50]}")
        logging.info(f"[Claude] Размер промпта: {len(full_prompt)} символов")
        
        try:
            logging.info("[ClaudeService] Отправка запроса в Claude API...")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.endpoint,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": full_prompt
                            }
                        ],
                        "temperature": 0.05,
                        "max_tokens": 2000
                    }
                )
                
                response_time_ms = int((time.time() - start_time) * 1000)
                
                if response.status_code == 200:
                    result = response.json()
                    answer = result['choices'][0]['message']['content']
                    logging.info(f"[ClaudeService] Ответ получен за {response_time_ms}ms")
                    return answer, response_time_ms
                else:
                    logging.error(f"[ClaudeService] Claude API error: {response.status_code} - {response.text}")
                    return self._error_response(), response_time_ms
                        
        except httpx.TimeoutException:
            logging.error("[ClaudeService] Claude API timeout")
            return "⏱️ Превышено время ожидания ответа. Попробуйте упростить вопрос.", int((time.time() - start_time) * 1000)
            
        except Exception as e:
            logging.error(f"[ClaudeService] Exception: {e}", exc_info=True)
            return self._error_response(), int((time.time() - start_time) * 1000)
    
    def _build_context(self, docs: list) -> str:
        """Формирование контекста из документов"""
        context_parts = []
        for doc in docs[:3]:
            title = doc.get('question', 'Без названия')
            answer = doc.get('answer', '')
            source = doc.get('source_file', '')
            combined = f"Вопрос: {title}\n\nОтвет: {answer}\n\nИсточник: {source}"
            snippet = combined[:1500] if len(combined) > 1500 else combined
            # ИСПРАВЛЕНО: Убрали эмодзи 📄
            context_parts.append(f"ДОКУМЕНТ: {title}\n\n{snippet}")
        return "\n\n" + "="*60 + "\n\n".join(context_parts)
    
    def _build_full_prompt(self, query: str, context: str) -> str:
        """Формирование полного промпта"""
        return f"""Ты — профессиональный AI-ассистент по системе ЕАСУЗ 44-ФЗ.

🎯 ГЛАВНОЕ ПРАВИЛО:
Ты ДОЛЖЕН давать полезный ответ на основе предоставленных документов ниже.
НИКОГДА не говори "информации нет" или "инструкции не найдены", если документы предоставлены.
ВСЕГДА находи в документах полезную информацию и формулируй на её основе четкий ответ.

📋 АЛГОРИТМ РАБОТЫ:
1. Внимательно изучи ВСЕ документы ниже
2. Найди информацию, относящуюся к вопросу пользователя
3. Сформулируй четкий, структурированный ответ
4. Используй Markdown: заголовки (##), списки (•), **жирный текст**, *курсив*
5. Укажи источник документа в конце ответа В HTML ФОРМАТЕ
6. Если есть пошаговые инструкции — перечисли их подробно

📚 ДОКУМЕНТЫ ИЗ БАЗЫ ЗНАНИЙ:
{context}

❓ ВОПРОС ПОЛЬЗОВАТЕЛЯ:
{query}

💡 СТРУКТУРА ТВОЕГО ОТВЕТА:
## Заголовок (краткий ответ)

Подробное объяснение...

### Пошаговая инструкция (если применимо):
1. Шаг первый...
2. Шаг второй...

<b>Источник:</b> Название_документа.расширение

💡 **Рекомендация:** ...

⚠️⚠️⚠️ КРИТИЧНО: ФОРМАТИРОВАНИЕ ⚠️⚠️⚠️

ДЛЯ ОСНОВНОГО ТЕКСТА ИСПОЛЬЗУЙ MARKDOWN:
✅ ## Заголовок
✅ ### Подзаголовок
✅ **жирный текст**
✅ *курсив*
✅ - списки
✅ 1. нумерованные списки

ТОЛЬКО ДЛЯ ИСТОЧНИКА ИСПОЛЬЗУЙ HTML:
✅ <b>Источник:</b> Название.расширение
✅ <b>Рекомендация:</b> текст

ФОРМАТ ИСТОЧНИКА:
<b>Источник:</b> Название_файла.расширение

ПРАВИЛА ИСТОЧНИКА:
1. ✅ ТОЛЬКО HTML-тег для слова "Источник": <b>Источник:</b>
2. ✅ Пробел после закрывающего тега </b>
3. ✅ Полное название файла с расширением на той же строке
4. ❌ БЕЗ эмодзи 📄
5. ❌ БЕЗ тире "- "
6. ❌ БЕЗ переноса на новую строку (всё в одну строку!)
7. ❌ БЕЗ множественного числа "Источники:"
8. ✅ ТОЛЬКО ОДИН источник (самый релевантный)
9. ❌ НЕ ИСПОЛЬЗУЙ <b> в основном тексте - только в источнике!

❌ НЕПРАВИЛЬНЫЕ ПРИМЕРЫ:
📄 Источник: ...
Источник: - ...
<b>Источники:</b> ...
- <b>Источник:</b> ...
<b>Источник:</b>
Название.xlsx (перенос - НЕПРАВИЛЬНО!)
Нажмите <b>Кнопку</b> (НЕ используй HTML в тексте!)

✅ ПРАВИЛЬНЫЕ ПРИМЕРЫ:
Основной текст: Нажмите **Кнопку** (Markdown!)
Источник: <b>Источник:</b> Инструкция.docx (HTML!)

✅ ПРИМЕР ИДЕАЛЬНОГО ОТВЕТА:
"## Создание плана-графика

Для создания плана-графика в ЕАСУЗ 44-ФЗ выполните следующие действия:

### Шаг 1: Вход в систему
- Откройте раздел **"План-график"**
- Нажмите **"Создать новый"**

### Шаг 2: Заполнение
- Укажите период планирования
- Добавьте позиции закупок
...

<b>Источник:</b> Инструкция по созданию плана-графика.pdf

💡 **Рекомендация:** Рекомендуется проверить все обязательные поля перед сохранением."

ОТВЕЧАЙ СЕЙЧАС:"""
    
    def _no_docs_response(self) -> str:
        """Ответ когда документы не найдены"""
        return """К сожалению, по вашему запросу ничего не найдено в базе знаний.

Попробуйте:
- Переформулировать вопрос проще
- Использовать ключевые слова (например: "заявка", "закупка", "план-график")
- Выбрать категорию из главного меню"""
    
    def _error_response(self) -> str:
        """Ответ при ошибке API"""
        return """❌ Произошла ошибка при обработке запроса.

Попробуйте:
- Повторить запрос через минуту
- Упростить формулировку вопроса
- Выбрать категорию из меню

Если проблема повторяется — обратитесь к администратору."""