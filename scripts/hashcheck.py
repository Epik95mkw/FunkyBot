import fnmatch
import os

from dotenv import load_dotenv

from api.spreadsheet_old import Spreadsheet
from api.wiimms_tools import wszst
from core import paths

PATH = paths.CTGP


async def hash_check(sheet: Spreadsheet) -> list[tuple]:
    lb_sha1s = sheet[1].read_col('SHA1')
    tracks = [t for t in os.listdir(PATH) if t[0] != '_']
    incorrect = []

    for i, track in enumerate(tracks):
        szs = fnmatch.filter(os.listdir(PATH + track), '*.szs')[0]
        sha1 = await wszst.sha1(PATH + track + '/' + szs)
        sha1 = sha1.split()[0].upper()
        if sha1 != lb_sha1s[i]:
            incorrect.append((track, lb_sha1s[i]))

    return incorrect


async def main():
    load_dotenv()
    s = Spreadsheet(os.getenv('SHEETS_KEY'), '../token.json')

    print('Tracks with non-matching SHA1s:')
    incorrect = await hash_check(s)
    for t in incorrect:
        print(t[0])


if __name__ == '__main__':
    main()
