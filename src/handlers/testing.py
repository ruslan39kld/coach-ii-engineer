import json
import sqlite3
import logging
from aiogram import types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import sanitize_markdown, split_lesson_into_sections
import config

# Глобальное хранилище состояния тестирования
user_test_state = {}

def get_tests_from_db(module_no: int, lesson_no: int) -> list:
    """Загрузка тестов из БД для конкретного урока"""
    try:
        db_path = config.DB_PATH
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, question_number, question_text, options, correct_answers, explanations, is_multiple_choice
            FROM tests
            WHERE module_no = ? AND lesson_no = ?
            ORDER BY question_number
        """, (module_no, lesson_no))
        
        rows = cursor.fetchall()
        conn.close()
        
        tests = []
        for row in rows:
            tests.append({
                'id': row[0],
                'question_number': row[1],
                'question_text': row[2],
                'options': json.loads(row[3]),
                'correct_answers': json.loads(row[4]),
                'explanations': json.loads(row[5]),
                'is_multiple_choice': bool(row[6])
            })
        
        return tests
    except Exception as e:
        logging.error(f"❌ Ошибка загрузки тестов: {e}")
        return []

async def start_test(callback: CallbackQuery, db, user_id: int):
    """Запуск тестирования"""
    from handlers.learning import user_modes
    
    # Получаем текущий урок
    m_no, l_no, _ = db.get_user_progress(user_id)
    
    # Загружаем тесты
    tests = get_tests_from_db(m_no, l_no)
    
    if not tests:
        await callback.message.edit_text(
            "⚠️ Тесты для этого урока еще не загружены.\n"
            "Переходим к следующему уроку.",
            parse_mode="Markdown"
        )
        await complete_lesson_after_test(callback, db, user_id)
        await callback.answer()
        return
    
    # Инициализируем состояние тестирования
    user_test_state[user_id] = {
        'module_no': m_no,
        'lesson_no': l_no,
        'attempt': 1,
        'current_question': 1,
        'answers': {},
        'correct_count': 0,
        'test_message_id': callback.message.message_id, # Сохраняем ID сообщения, в котором начинается тест
        'chat_id': callback.message.chat.id # Сохраняем chat_id для будущих редактирований
    }
    
    # Переводим пользователя в режим тестирования
    user_modes[user_id] = "testing"
    
    # Редактируем текущее сообщение, чтобы начать тест
    await callback.message.edit_text(
        f"📝 *ТЕСТ ПО УРОКУ {l_no}*\n\n"
        f"Вам нужно ответить на 3 вопроса.\n"
        f"Для успешного прохождения необходимо правильно ответить на 2 из 3 вопросов.\n\n"
        f"У вас есть 2 попытки.\n\n"
        f"Начинаем! 🚀",
        parse_mode="Markdown"
    )
    
    # Показываем первый вопрос (редактируем то же самое сообщение)
    await show_test_question(callback, user_id)
    await callback.answer()

async def show_test_question(callback: CallbackQuery, user_id: int):
    """Показ текущего вопроса теста (редактируем существующее сообщение)"""
    state = user_test_state.get(user_id)
    
    if not state:
        await callback.message.answer("⚠️ Ошибка: состояние теста не найдено")
        return
    
    m_no = state['module_no']
    l_no = state['lesson_no']
    current_q = state['current_question']
    attempt = state['attempt']
    
    # Загружаем тесты
    tests = get_tests_from_db(m_no, l_no)
    
    if not tests or current_q > len(tests):
        await callback.message.answer("⚠️ Ошибка загрузки вопроса")
        return
    
    test = tests[current_q - 1]
    
    # Формируем текст вопроса
    question_text = f"*❓ Вопрос {current_q} из 3*\n"
    question_text += f"_Попытка {attempt} из 2_\n\n"
    question_text += f"{test['question_text']}\n\n"
    
    # Добавляем варианты ответов
    for i, option in enumerate(test['options'], 1):
        question_text += f"{i}. {option}\n"
    
    question_text += f"\n*Введите номер ответа:*"
    
    # РЕДАКТИРУЕМ СООБЩЕНИЕ, В КОТОРОМ НАХОДИМСЯ
    try:
        await callback.bot.edit_message_text(
            chat_id=state['chat_id'],
            message_id=state['test_message_id'],
            text=question_text,
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"❌ Ошибка редактирования сообщения с вопросом: {e}")
        # Если редактирование не удалось (например, сообщение было удалено), отправляем новое
        sent_message = await callback.message.answer(question_text, parse_mode="Markdown")
        state['test_message_id'] = sent_message.message_id
        state['chat_id'] = sent_message.chat.id

async def handle_test_answer(message: types.Message, db):
    """Обработка ответа на вопрос теста"""
    user_id = message.from_user.id
    state = user_test_state.get(user_id)
    
    if not state:
        await message.answer("⚠️ Ошибка: тест не найден. Начните заново через /start")
        return
    
    m_no = state['module_no']
    l_no = state['lesson_no']
    current_q = state['current_question']
    
    # Загружаем тесты
    tests = get_tests_from_db(m_no, l_no)
    
    if not tests or current_q > len(tests):
        await message.answer("⚠️ Ошибка загрузки теста")
        return
    
    test = tests[current_q - 1]
    
    # Парсим ответ пользователя
    try:
        user_answer = int(message.text.strip())
    except ValueError:
        # Отправляем сообщение об ошибке, но не редактируем основное
        error_msg = await message.answer("⚠️ Введите номер ответа (цифру)")
        # Удаляем сообщение пользователя и сообщение об ошибке через короткое время
        try:
            await message.delete()
            await error_msg.delete()
        except:
            pass
        return
    
    # Проверяем валидность ответа
    if user_answer < 1 or user_answer > len(test['options']):
        error_msg = await message.answer(f"⚠️ Введите номер от 1 до {len(test['options'])}")
        try:
            await message.delete()
            await error_msg.delete()
        except:
            pass
        return
    
    # Сохраняем ответ
    state['answers'][current_q] = user_answer
    
    # Проверяем правильность
    correct_answers = test['correct_answers']
    is_correct = user_answer in correct_answers
    
    if is_correct:
        state['correct_count'] += 1
    
    # Формируем ответ с подсветкой и объяснением
    if is_correct:
        response = f"🟢 *ПРАВИЛЬНО!*\n\n"
        response += f"✅ {test['options'][user_answer - 1]}\n\n"
        
        # Объяснение правильного ответа
        explanation_key = str(user_answer)
        if explanation_key in test['explanations']:
            response += f"💡 *Пояснение:*\n{test['explanations'][explanation_key]}"
    else:
        response = f"🔴 *НЕПРАВИЛЬНО*\n\n"
        response += f"❌ Ваш ответ: {test['options'][user_answer - 1]}\n\n"
        
        # Показываем правильный ответ
        correct_num = correct_answers[0]
        response += f"✅ *Правильный ответ:*\n{test['options'][correct_num - 1]}\n\n"
        
        # Объяснение правильного ответа
        correct_key = str(correct_num)
        if correct_key in test['explanations']:
            response += f"💡 *Почему это правильно:*\n{test['explanations'][correct_key]}\n\n"
        
        # Объяснение неправильного ответа
        wrong_key = str(user_answer)
        if wrong_key in test['explanations']:
            response += f"❗️ *Почему ваш ответ неверен:*\n{test['explanations'][wrong_key]}"
    
    # Определяем, какую кнопку показать
    if current_q < 3:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Следующий вопрос", callback_data="next_test_question")]
        ])
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Показать результат", callback_data="show_test_result")]
        ])
    
    # Удаляем сообщение пользователя с ответом
    try:
        await message.delete()
    except:
        pass
    
    # РЕДАКТИРУЕМ ОСНОВНОЕ СООБЩЕНИЕ ТЕСТА
    try:
        await message.bot.edit_message_text(
            chat_id=state['chat_id'],
            message_id=state['test_message_id'],
            text=response,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"❌ Ошибка редактирования сообщения с ответом: {e}")
        # Если редактирование не удалось, отправляем новое сообщение и обновляем state
        sent_message = await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")
        state['test_message_id'] = sent_message.message_id
        state['chat_id'] = sent_message.chat.id

async def next_test_question(callback: CallbackQuery, user_id: int):
    """Переход к следующему вопросу теста (редактируем существующее сообщение)"""
    state = user_test_state.get(user_id)
    
    if not state:
        await callback.answer("⚠️ Ошибка: тест не найден")
        return
    
    # Увеличиваем номер вопроса
    state['current_question'] += 1
    
    # РЕДАКТИРУЕМ ОСНОВНОЕ СООБЩЕНИЕ ТЕСТА
    await show_test_question(callback, user_id)
    await callback.answer()

async def show_test_result(callback: CallbackQuery, db, user_id: int):
    """Показ результата теста с логикой попыток (редактируем существующее сообщение)"""
    from handlers.learning import user_modes
    
    state = user_test_state.get(user_id)
    
    if not state:
        await callback.answer("⚠️ Ошибка: тест не найден")
        return
    
    m_no = state['module_no']
    l_no = state['lesson_no']
    attempt = state['attempt']
    correct = state['correct_count']
    answers = state['answers']
    
    # Сохраняем попытку в БД
    try:
        conn = sqlite3.connect(config.DB_PATH)
        cursor = conn.cursor()
        
        passed = correct >= 2
        
        cursor.execute("""
            INSERT INTO user_test_attempts (user_id, module_no, lesson_no, attempt_number, answers, score, passed)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, m_no, l_no, attempt, json.dumps(answers), correct, passed))
        
        conn.commit()
        conn.close()
        
        logging.info(f"✅ Сохранена попытка {attempt} для пользователя {user_id}, урок {m_no}.{l_no}, результат: {correct}/3")
    except Exception as e:
        logging.error(f"❌ Ошибка сохранения попытки: {e}")
    
    # Формируем результат
    result_text = f"*📊 РЕЗУЛЬТАТ ТЕСТА*\n\n"
    result_text += f"Модуль {m_no}, Урок {l_no}\n"
    result_text += f"Попытка {attempt} из 2\n\n"
    result_text += f"*Правильных ответов:* {correct} из 3\n\n"
    
    # Проверяем, сдал ли тест
    if correct >= 2:
        result_text += "🎉 *ПОЗДРАВЛЯЕМ!*\n\n"
        result_text += "Тест успешно пройден!\n"
        result_text += "Можете переходить к следующему уроку."
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Завершить урок", callback_data="complete_lesson_after_test")],
            [InlineKeyboardButton(text="📋 Список уроков", callback_data="lesson_list")]
        ])
        
        # Очищаем состояние теста
        if user_id in user_test_state:
            del user_test_state[user_id]
        
        # Возвращаем режим обучения
        user_modes[user_id] = "learning"
        
    else:
        if attempt < 2:
            result_text += "❌ *Тест не пройден*\n\n"
            result_text += "Для успешного прохождения нужно правильно ответить минимум на 2 вопроса из 3.\n\n"
            result_text += "У вас есть еще одна попытка!"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Попытка 2", callback_data="retry_test")],
                [InlineKeyboardButton(text="📋 Список уроков", callback_data="lesson_list")]
            ])
        else:
            result_text += "❌ *Тест не пройден*\n\n"
            result_text += "Вы использовали все попытки (2 из 2).\n\n"
            result_text += "Рекомендуем пройти урок заново и повторить материал."
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📖 Пройти урок заново", callback_data="retake_lesson")],
                [InlineKeyboardButton(text="📋 Список уроков", callback_data="lesson_list")]
            ])
            
            # Очищаем состояние теста
            if user_id in user_test_state:
                del user_test_state[user_id]
            
            # Возвращаем режим обучения
            user_modes[user_id] = "learning"
    
    # РЕДАКТИРУЕМ ОСНОВНОЕ СООБЩЕНИЕ ТЕСТА
    try:
        await callback.bot.edit_message_text(
            chat_id=state['chat_id'],
            message_id=state['test_message_id'],
            text=result_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"❌ Ошибка редактирования сообщения с результатом: {e}")
        # Если редактирование не удалось, отправляем новое сообщение и обновляем state
        sent_message = await callback.message.answer(result_text, reply_markup=keyboard, parse_mode="Markdown")
        state['test_message_id'] = sent_message.message_id
        state['chat_id'] = sent_message.chat.id
    
    await callback.answer()

async def retry_test(callback: CallbackQuery, user_id: int):
    """Вторая попытка прохождения теста (редактируем существующее сообщение)"""
    from handlers.learning import user_modes
    
    state = user_test_state.get(user_id)
    
    if not state:
        await callback.answer("⚠️ Ошибка: тест не найден")
        return
    
    # Сбрасываем на вторую попытку
    state['attempt'] = 2
    state['current_question'] = 1
    state['answers'] = {}
    state['correct_count'] = 0
    
    # Переводим в режим тестирования
    user_modes[user_id] = "testing"
    
    # РЕДАКТИРУЕМ ОСНОВНОЕ СООБЩЕНИЕ ТЕСТА
    try:
        await callback.bot.edit_message_text(
            chat_id=state['chat_id'],
            message_id=state['test_message_id'],
            text=f"🔄 *ПОПЫТКА 2*\n\n"
                 f"Начинаем второй раз. Вы можете это сделать! 💪",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"❌ Ошибка редактирования сообщения для второй попытки: {e}")
        # Если редактирование не удалось, отправляем новое сообщение и обновляем state
        sent_message = await callback.message.answer(f"🔄 *ПОПЫТКА 2*\n\n"
                                                     f"Начинаем второй раз. Вы можете это сделать! 💪",
                                                     parse_mode="Markdown")
        state['test_message_id'] = sent_message.message_id
        state['chat_id'] = sent_message.chat.id
    
    # Показываем первый вопрос (редактируем то же самое сообщение)
    await show_test_question(callback, user_id)
    await callback.answer()

async def retake_lesson(callback: CallbackQuery, db, user_id: int):
    """Возврат к началу урока (раздел 1)"""
    from handlers.learning import user_modes
    
    # Получаем текущий урок
    m_no, l_no, _ = db.get_user_progress(user_id)
    
    # Сбрасываем на раздел 0
    db.update_user_progress(user_id, m_no, l_no, 0)
    
    # Загружаем урок
    lesson = db.get_lesson(m_no, l_no)
    
    if not lesson:
        await callback.answer("Ошибка загрузки урока")
        return
    
    title, content, _ = lesson
    sections = split_lesson_into_sections(content)
    section_text = sections[0]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Следующий раздел", callback_data="next_section")],
        [InlineKeyboardButton(text="📋 Список уроков", callback_data="lesson_list")]
    ])
    
    # Возвращаем режим обучения
    user_modes[user_id] = "learning"
    
    # РЕДАКТИРУЕМ ОСНОВНОЕ СООБЩЕНИЕ ТЕСТА
    try:
        await callback.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=f"📖 *Начинаем урок заново*\n\n"
                 f"*Модуль {m_no}, Урок {l_no}*\n"
                 f"*{title}*\n\n{section_text}\n\n"
                 f"_Раздел 1 из {len(sections)}_",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"❌ Ошибка редактирования сообщения при возврате к уроку: {e}")
        # Если редактирование не удалось, отправляем новое сообщение
        await callback.message.edit_text(f"📖 *Начинаем урок заново*\n\n"
                                         f"*Модуль {m_no}, Урок {l_no}*\n"
                                         f"*{title}*\n\n{section_text}\n\n"
                                         f"_Раздел 1 из {len(sections)}_",
                                         reply_markup=keyboard,
                                         parse_mode="Markdown")
    
    await callback.answer()

async def complete_lesson_after_test(callback: CallbackQuery, db, user_id: int):
    """Завершение урока после успешного прохождения теста"""
    m_no, l_no, _ = db.get_user_progress(user_id)
    
    # Отмечаем урок как завершенный
    db.mark_lesson_completed(user_id, m_no, l_no)
    
    lesson = db.get_lesson(m_no, l_no)
    title = lesson[0] if lesson else f"Урок {l_no}"
    
    # ПЕРЕХОДИМ НА СЛЕДУЮЩИЙ УРОК
    l_no += 1
    lesson = db.get_lesson(m_no, l_no)
    
    if not lesson:
        m_no += 1
        l_no = 1
        lesson = db.get_lesson(m_no, l_no)
    
    if not lesson:
        # Курс завершен - показываем статистику
        await show_course_statistics(callback, db, user_id)
        return
    
    # Сбрасываем на первый раздел нового урока
    db.update_user_progress(user_id, m_no, l_no, 0)
    
    new_title, new_content, _ = lesson
    sections = split_lesson_into_sections(new_content)
    section_text = sections[0]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Следующий раздел", callback_data="next_section")],
        [InlineKeyboardButton(text="📋 Список уроков", callback_data="lesson_list")]
    ])
    
    # РЕДАКТИРУЕМ ОСНОВНОЕ СООБЩЕНИЕ ТЕСТА
    try:
        await callback.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=f"✅ *Урок {m_no}.{l_no-1} завершен!*\n\n"
                 f"📖 *Модуль {m_no}, Урок {l_no}*\n"
                 f"*{new_title}*\n\n{section_text}\n\n"
                 f"_Раздел 1 из {len(sections)}_",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"❌ Ошибка редактирования сообщения при завершении урока: {e}")
        # Если редактирование не удалось, отправляем новое сообщение
        await callback.message.edit_text(f"✅ *Урок {m_no}.{l_no-1} завершен!*\n\n"
                                         f"📖 *Модуль {m_no}, Урок {l_no}*\n"
                                         f"*{new_title}*\n\n{section_text}\n\n"
                                         f"_Раздел 1 из {len(sections)}_",
                                         reply_markup=keyboard,
                                         parse_mode="Markdown")
    
    await callback.answer()

async def show_course_statistics(callback: CallbackQuery, db, user_id: int):
    """Показ общей статистики по курсу"""
    try:
        conn = sqlite3.connect(config.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT module_no, lesson_no, attempt_number, score, passed
            FROM user_test_attempts
            WHERE user_id = ?
            ORDER BY module_no, lesson_no, attempt_number
        """, (user_id,))
        
        attempts = cursor.fetchall()
        conn.close()
        
        total_lessons = 23
        passed_lessons = set()
        total_attempts = len(attempts)
        total_correct = 0
        first_try_passes = 0
        
        for attempt in attempts:
            m_no, l_no, attempt_num, score, passed = attempt
            total_correct += score
            
            if passed:
                passed_lessons.add((m_no, l_no))
                if attempt_num == 1:
                    first_try_passes += 1
        
        passed_count = len(passed_lessons)
        total_questions = total_attempts * 3
        avg_score = (total_correct / total_questions * 100) if total_questions > 0 else 0
        
        stats_text = f"🎉 *ПОЗДРАВЛЯЕМ!*\n\n"
        stats_text += f"Вы завершили весь курс промт-инжиниринга!\n\n"
        stats_text += f"*📊 ОБЩАЯ СТАТИСТИКА:*\n\n"
        stats_text += f"✅ Пройдено уроков: {passed_count}/{total_lessons}\n"
        stats_text += f"📝 Всего попыток: {total_attempts}\n"
        stats_text += f"🎯 Средний балл: {avg_score:.1f}%\n"
        stats_text += f"⭐️ Сдано с первой попытки: {first_try_passes}\n\n"
        
        if passed_count == total_lessons:
            stats_text += f"🏆 *Вы прошли все {total_lessons} урока!*\n\n"
            stats_text += f"Теперь вы владеете навыками промт-инжиниринга и можете эффективно работать с ИИ-инструментами!"
        else:
            stats_text += f"💡 Осталось пройти: {total_lessons - passed_count} уроков"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Список уроков", callback_data="lesson_list")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        # РЕДАКТИРУЕМ ОСНОВНОЕ СООБЩЕНИЕ ТЕСТА
        try:
            await callback.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=stats_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"❌ Ошибка редактирования сообщения со статистикой: {e}")
            # Если редактирование не удалось, отправляем новое сообщение
            await callback.message.edit_text(stats_text, reply_markup=keyboard, parse_mode="Markdown")
        
    except Exception as e:
        logging.error(f"❌ Ошибка загрузки статистики: {e}")
        # РЕДАКТИРУЕМ ОСНОВНОЕ СООБЩЕНИЕ ТЕСТА
        try:
            await callback.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="🎉 *ПОЗДРАВЛЯЕМ!*\n\n"
                     "Вы завершили весь курс промт-инжиниринга!",
                parse_mode="Markdown"
            )
        except Exception as e2:
            logging.error(f"❌ Ошибка редактирования сообщения со статистикой (fallback): {e2}")
            # Если редактирование не удалось, отправляем новое сообщение
            await callback.message.edit_text("🎉 *ПОЗДРАВЛЯЕМ!*\n\n"
                                             "Вы завершили весь курс промт-инжиниринга!",
                                             parse_mode="Markdown")
    
    await callback.answer()