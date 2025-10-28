from pathlib import Path
import pandas as pd

DATA_FOLDER = Path("data")

print("Checking files...")
print(f"Folder exists: {DATA_FOLDER.exists()}")

files = list(DATA_FOLDER.glob("*.xlsx"))
print(f"Found {len(files)} Excel files")

if files:
    print("\nFirst 5 files:")
    for i, f in enumerate(files[:5], 1):
        print(f"{i}. {f.name}")
        
    print("\nTrying to read first file...")
    try:
        df = pd.read_excel(str(files[0]))
        print(f"OK! Rows: {len(df)}, Columns: {list(df.columns)}")
    except Exception as e:
        print(f"ERROR: {e}")
else:
    print("No Excel files found!")

input("Press Enter...")