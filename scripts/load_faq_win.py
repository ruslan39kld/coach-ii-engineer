# -*- coding: utf-8 -*-
import pandas as pd
import sqlite3
from pathlib import Path
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

DATA_FOLDER = Path("data")
DB_FILE = Path("data/bot.db")

print("="*60)
print("LOADING FAQ")
print("="*60)

excel_files = list(DATA_FOLDER.glob("*.xlsx"))
print(f"Found {len(excel_files)} files\n")

conn = sqlite3.connect(str(DB_FILE))
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS faq (
        id INTEGER PRIMARY KEY,
        question TEXT,
        answer TEXT,
        source_file TEXT
    )
""")

cursor.execute("DELETE FROM faq")
conn.commit()

total = 0
files_with_data = 0

for f in excel_files:
    try:
        # Try reading with header at row 1 (0-indexed)
        df = pd.read_excel(str(f), header=1)
        
        # Look for question and answer columns
        question_col = None
        answer_col = None
        
        # Check for different possible column names
        for col in df.columns:
            col_str = str(col).strip().lower()
            if 'вопрос' in col_str:
                question_col = col
            elif 'ответ' in col_str:
                answer_col = col
        
        if question_col is not None and answer_col is not None:
            file_questions = 0
            for _, row in df.iterrows():
                q = str(row.get(question_col, '')).strip()
                a = str(row.get(answer_col, '')).strip()
                
                # Filter out empty, nan, or too short questions
                if (q and a and 
                    len(q) > 5 and 
                    q.lower() != 'nan' and 
                    a.lower() != 'nan' and
                    q.lower() != 'none' and 
                    a.lower() != 'none'):
                    
                    cursor.execute(
                        "INSERT INTO faq (question, answer, source_file) VALUES (?, ?, ?)", 
                        (q, a, f.name)
                    )
                    total += 1
                    file_questions += 1
            
            conn.commit()
            if file_questions > 0:
                print(f" OK: {f.name} ({file_questions} questions)")
                files_with_data += 1
            else:
                print(f" EMPTY: {f.name} (no valid Q&A found)")
        else:
            print(f" SKIP: {f.name} (columns not found: Q={question_col}, A={answer_col})")
            
    except Exception as e:
        print(f" ERROR: {f.name} - {e}")

conn.close()

print("\n" + "="*60)
print(f"DONE! Loaded: {total}+ questions from {files_with_data} files")
print("="*60)

try:
    input("\nPress Enter to exit...")
except EOFError:
    pass