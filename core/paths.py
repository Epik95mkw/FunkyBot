import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
MAIN = Path(os.getenv('CT_PATH'))

CTGP = MAIN / 'CTGP Tracks'
REGS = MAIN / 'Original Tracks'
TEMP = MAIN / 'temp'

def clear_temp():
    if len(os.listdir(TEMP)) > 0:
        for f in os.listdir(TEMP):
            os.remove(TEMP / f)
