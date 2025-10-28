#!/usr/bin/env python3
"""Start bot with verbose console output"""

import asyncio
import logging
import sys
import os

# Force UTF-8 output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Setup logging to console only
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

print("="*60)
print("STARTING EASUZ BOT")
print("="*60)

# Import and run the bot
from bot import async_main

if __name__ == '__main__':
    try:
        print("\n[INFO] Initializing bot...")
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n[INFO] Bot stopped by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
