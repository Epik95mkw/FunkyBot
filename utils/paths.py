import os
from dotenv import load_dotenv

load_dotenv()
MAIN = os.getenv('CTPATH')
CTGP = MAIN + 'CTGP Tracks/'
REGS = MAIN + 'Original Tracks/'
TEMP = MAIN + 'temp/'
