@echo off
chcp 65001 > nul
:menu
cls
echo ============================================================
echo           МЕНЮ ЗАПУСКА БОТА ЕАСУЗ
echo ============================================================
echo.
echo Выберите режим работы:
echo.
echo 1. Запустить бота в Telegram (требует VPN/прокси)
echo 2. Локальное тестирование с AI (требует интернет для Claude)
echo 3. Тестирование FAQ базы (работает офлайн)
echo 4. Загрузить FAQ из Excel файлов
echo 5. Проверить статистику базы данных
echo 6. Выход
echo.
echo ============================================================
set /p choice="Введите номер (1-6): "

if "%choice%"=="1" goto telegram
if "%choice%"=="2" goto local_ai
if "%choice%"=="3" goto faq_test
if "%choice%"=="4" goto load_faq
if "%choice%"=="5" goto stats
if "%choice%"=="6" goto end

echo.
echo Неверный выбор! Попробуйте снова.
timeout /t 2 > nul
goto menu

:telegram
cls
echo ============================================================
echo ЗАПУСК БОТА В TELEGRAM
echo ============================================================
echo.
echo ВНИМАНИЕ: Требуется VPN или прокси для доступа к Telegram API
echo.
pause
python run.py
pause
goto menu

:local_ai
cls
echo ============================================================
echo ЛОКАЛЬНОЕ ТЕСТИРОВАНИЕ С AI
echo ============================================================
echo.
python test_bot_local.py
pause
goto menu

:faq_test
cls
echo ============================================================
echo ТЕСТИРОВАНИЕ FAQ БАЗЫ (ОФЛАЙН)
echo ============================================================
echo.
python test_faq_simple.py
pause
goto menu

:load_faq
cls
echo ============================================================
echo ЗАГРУЗКА FAQ ИЗ EXCEL
echo ============================================================
echo.
python load_faq_win.py
pause
goto menu

:stats
cls
echo ============================================================
echo СТАТИСТИКА БАЗЫ ДАННЫХ
echo ============================================================
echo.
python verify_db.py
pause
goto menu

:end
cls
echo.
echo Спасибо за использование!
echo.
timeout /t 2 > nul
exit
