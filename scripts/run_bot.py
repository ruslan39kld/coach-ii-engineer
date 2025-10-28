#!/usr/bin/env python3
"""Simple bot runner with console output"""

import os
os.environ['PYTHONUNBUFFERED'] = '1'

print("="*60)
print("EASUZ 44-FZ BOT STARTING...")
print("="*60)
print()

try:
    from bot import main
    main()
except Exception as e:
    print(f"\n[CRITICAL ERROR] {e}")
    import traceback
    traceback.print_exc()
    input("\nPress Enter to exit...")
