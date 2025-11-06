# ЕАСУЗ 44-ФЗ Бот

AI-консультант для работы с системой ЕАСУЗ на основе Claude AI

## Описание

Telegram-бот предоставляет профессиональные консультации по работе с системой ЕАСУЗ 44-ФЗ, используя базу знаний из документов на Яндекс.Диске и AI-модель Claude.

## Особенности

- ✅ Поэтапные инструкции
- ✅ База знаний на Яндекс.Диске
- ✅ SQLite с persistenceMount (данные не теряются)
- ✅ Автоматическая загрузка документов при запуске
- ✅ История запросов пользователей
- ✅ Деплой на Amvera.ru

## Локальный запуск

### 1. Установка зависимостей
```bash
pip install -r requirements_rag.txt
```

### 2. Настройка переменных окружения

Создайте файл `.env`:
```
TELEGRAM_BOT_TOKEN=your_token
ANTHROPIC_API_KEY=your_key
YADISK_TOKEN=your_yadisk_token
```

### 3. Запуск бота
```bash
python src/bot.py
```

## Деплой на Amvera

1. Подключите GitHub репозиторий
2. Настройте переменные окружения
3. Amvera автоматически использует `amvera.yml`

## Структура проекта
```
easuz_bot_deployer/
├── src/              # Исходный код
├── data/             # База данных и индексы
├── docs/             # Документация
├── requirements_rag.txt
└── amvera.yml
```

## Технологии

- Python 3.11
- python-telegram-bot
- Claude AI (Anthropic)
- FAISS + BM25 (гибридный поиск)
- SQLite