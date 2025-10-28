# improved_indexer.py - ПРАВИЛЬНАЯ индексация с DOCX таблицами и Q&A
import json
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import PyPDF2
import docx
from docx.table import Table
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl

import sys
sys.stdout = sys.stderr  # Принудительный вывод в stderr
print("SCRIPT LOADED!", flush=True)

class Config:
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    EXCEL_DIR = DATA_DIR / "excel_qa"
    INSTRUCTIONS_DIR = DATA_DIR / "instructions"
    INSTRUCTIONSPIP_DIR = DATA_DIR / "instructionspip"
    QA_JSON = DATA_DIR / "structured_qa.json"
    CHUNKS_JSON = DATA_DIR / "chunks_data.json"

def extract_text_from_word_IMPROVED(file_path):
    """
    Улучшенный парсинг DOCX:
    - Читает параграфы
    - Читает таблицы
    - Сохраняет структуру
    """
    try:
        doc = docx.Document(file_path)
        full_text = []
        
        for element in doc.element.body:
            if isinstance(element, CT_P):  # Параграф
                para = docx.text.paragraph.Paragraph(element, doc)
                if para.text.strip():
                    # Определяем заголовок
                    if para.style.name.startswith('Heading'):
                        full_text.append(f"\n## {para.text.strip()}\n")
                    else:
                        full_text.append(para.text.strip())
                        
            elif isinstance(element, CT_Tbl):  # Таблица
                table = docx.table.Table(element, doc)
                table_text = "\n[ТАБЛИЦА]\n"
                for row in table.rows:
                    row_text = " | ".join([cell.text.strip() for cell in row.cells])
                    if row_text.strip():
                        table_text += row_text + "\n"
                table_text += "[/ТАБЛИЦА]\n"
                full_text.append(table_text)
        
        return "\n".join(full_text)
    except Exception as e:
        print(f"Ошибка чтения {file_path}: {e}")
        return ""

def split_into_sections(text, filename):
    """
    Разбивает текст на разделы по заголовкам
    Возвращает список: [{"heading": "...", "content": "...", "source": "..."}]
    """
    sections = []
    current_heading = "Введение"
    current_content = []
    
    for line in text.split('\n'):
        if line.startswith('## '):  # Заголовок
            # Сохраняем предыдущий раздел
            if current_content:
                sections.append({
                    "heading": current_heading,
                    "content": '\n'.join(current_content).strip(),
                    "source": filename
                })
            # Новый раздел
            current_heading = line.replace('## ', '').strip()
            current_content = []
        else:
            if line.strip():
                current_content.append(line)
    
    # Последний раздел
    if current_content:
        sections.append({
            "heading": current_heading,
            "content": '\n'.join(current_content).strip(),
            "source": filename
        })
    
    return sections

def generate_qa_from_section(section, qa_id):
    """
    Генерирует Q&A из раздела документа
    """
    heading = section['heading']
    content = section['content']
    source = section['source']
    
    qa_pairs = []
    
    # Если заголовок - уже вопрос
    if any(word in heading.lower() for word in ['как', 'что', 'где', 'когда', 'почему', 'зачем']):
        qa_pairs.append({
            "id": f"qa_{qa_id:04d}",
            "question": heading,
            "answer": content[:500],  # Первые 500 символов
            "source": source,
            "category": "",
            "keywords": extract_keywords(heading + " " + content)
        })
        qa_id += 1
    
    # Специальные правила для ЧС
    if 'чс' in source.lower() or 'чрезвычайн' in content.lower():
        cs_questions = [
            "Как создать закупку при ЧС?",
            "С чего начать закупку при чрезвычайной ситуации?",
            "Какие документы нужны для ЧС?",
            "Ссылка на статью 44-ФЗ для ЧС?"
        ]
        for q in cs_questions:
            if not any(pair['question'] == q for pair in qa_pairs):
                qa_pairs.append({
                    "id": f"qa_{qa_id:04d}",
                    "question": q,
                    "answer": content[:500],
                    "source": source,
                    "category": "ЧС",
                    "keywords": extract_keywords(q + " чс чрезвычайная ситуация")
                })
                qa_id += 1
    
    # Правила для КРКС
    if 'кркс' in content.lower() or 'кркс' in heading.lower():
        if '0111' in content and '0112' in content:
            qa_pairs.append({
                "id": f"qa_{qa_id:04d}",
                "question": "Какой КРКС использовать для контракта прошлого года?",
                "answer": content[:500],
                "source": source,
                "category": "КРКС",
                "keywords": ["кркс", "0111", "0112", "контракт", "прошлый", "год"]
            })
            qa_id += 1
    
    # Правила для ГРБС
    if 'грбс' in content.lower() or 'грбс' in heading.lower():
        qa_pairs.append({
            "id": f"qa_{qa_id:04d}",
            "question": "Что такое ГРБС и какие функции выполняет?",
            "answer": content[:500],
            "source": source,
            "category": "ГРБС",
            "keywords": ["грбс", "главный", "распорядитель", "бюджет", "средства"]
        })
        qa_id += 1
    
    return qa_pairs, qa_id

def extract_keywords(text):
    """Извлекает ключевые слова"""
    stop_words = {'в', 'на', 'и', 'с', 'по', 'для', 'от', 'к', 'из', 'о', 'у', 'а', 'но'}
    words = [w.lower() for w in text.split() if len(w) > 3 and w.lower() not in stop_words]
    return list(dict.fromkeys(words))[:10]  # Уникальные, первые 10

def process_instructions_IMPROVED():
    """Улучшенная обработка инструкций"""
    print("\n📚 Обработка инструкций (УЛУЧШЕННАЯ)...")
    
    all_files = []
    for directory in [Config.INSTRUCTIONS_DIR, Config.INSTRUCTIONSPIP_DIR]:
        if directory.exists():
            all_files.extend(list(directory.glob("*.pdf")))
            all_files.extend(list(directory.glob("*.docx")))
    
    print(f"Найдено {len(all_files)} файлов")
    
    # Загружаем существующие Q&A
    existing_qa = []
    if Config.QA_JSON.exists():
        with open(Config.QA_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
            existing_qa = data.get('qa_pairs', [])
    
    qa_id = len(existing_qa) + 1
    new_qa_pairs = []
    chunks = []
    
    for file in tqdm(all_files, desc="Обработка"):
        try:
            # Извлекаем текст
            if file.suffix == '.docx':
                text = extract_text_from_word_IMPROVED(file)
            else:
                text = extract_text_from_pdf(file)  # Старая функция для PDF
            
            if not text:
                continue
            
            # Разбиваем на разделы
            sections = split_into_sections(text, file.name)
            
            # Генерируем Q&A из каждого раздела
            for section in sections:
                qa_pairs, qa_id = generate_qa_from_section(section, qa_id)
                new_qa_pairs.extend(qa_pairs)
                
                # Создаем chunk
                chunks.append({
                    "id": f"chunk_{len(chunks)+1:05d}",
                    "text": section['content'],
                    "source": file.name,
                    "heading": section['heading'],
                    "keywords": extract_keywords(section['heading'] + " " + section['content'])
                })
        
        except Exception as e:
            print(f"\nОшибка в {file.name}: {e}")
    
    # Объединяем с существующими Q&A
    all_qa = existing_qa + new_qa_pairs
    
    # Сохраняем
    with open(Config.QA_JSON, 'w', encoding='utf-8') as f:
        json.dump({"qa_pairs": all_qa}, f, ensure_ascii=False, indent=2)
    
    with open(Config.CHUNKS_JSON, 'w', encoding='utf-8') as f:
        json.dump({"chunks": chunks}, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Добавлено {len(new_qa_pairs)} новых Q&A")
    print(f"✅ Всего Q&A: {len(all_qa)}")
    print(f"✅ Chunks: {len(chunks)}")
    
    return all_qa, chunks

def extract_text_from_pdf(file_path):
    """Старая функция для PDF"""
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text
    except:
        return ""

if __name__ == "__main__":
    import sys
    print("START", file=sys.stderr)
    print("="*60)
    print("IMPROVED INDEXING STARTED")
    print("="*60)
    
    try:
        qa_pairs, chunks = process_instructions_IMPROVED()
        print(f"\nDONE: {len(qa_pairs)} QA, {len(chunks)} chunks")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()