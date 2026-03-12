import os

# Создаём папки если их нет
folders = [
    'handlers',
    'services', 
    'utils'
]

for folder in folders:
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"✅ Создана папка: {folder}")
    else:
        print(f"⚠️ Папка уже существует: {folder}")

# Создаём __init__.py файлы
init_files = [
    'handlers/__init__.py',
    'services/__init__.py',
    'utils/__init__.py'
]

for init_file in init_files:
    if not os.path.exists(init_file):
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write('# Auto-generated\n')
        print(f"✅ Создан файл: {init_file}")
    else:
        print(f"⚠️ Файл уже существует: {init_file}")

print("\n🎉 Структура создана!")