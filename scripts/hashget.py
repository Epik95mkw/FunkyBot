import asyncio
import fnmatch
import os
import shutil

import requests
from dotenv import load_dotenv

from api.spreadsheet_old import Spreadsheet
from wiimms_tools import *
from hashcheck import hash_check
from core import paths

PATH = paths.CTGP


async def download_wbz(path, sha1, tname=None):
    if tname is None:
        tname = sha1
    print(f'Downloading {tname}...')
    url = f'https://ct.wiimm.de/d/{sha1}'
    res = requests.get(url)
    if not res.ok:
        print(f'Failed to download wbz for {tname} (response code {res.status_code}: {res.reason})')
        return False

    with open(f'{path}/{tname}.wbz', 'wb') as f:
        f.write(res.content)
    return True


async def main(i=15):
    load_dotenv()
    print('Reading spreadsheet...')
    s = Spreadsheet(os.getenv('SHEETS_KEY'), '../token.json')

    path = PATH + '_FIX/'
    if not os.path.isdir(path):
        os.mkdir(path)

    print('Checking SHA1s...')
    incorrect = await hash_check(s)
    print(f'Found {len(incorrect)} files with incorrect SHA1s.')

    # TODO: fix wiimms tools calls
    for track, sha1 in incorrect[i:]:
        if not os.path.isdir(f'{path}{track}'):
            os.mkdir(f'{path}{track}')
        if not await download_wbz(path + track, sha1, track):
            shutil.rmtree(f'{path}{track}')
            continue
        if not await wszst.encode(f'{path}{track}/{track}.wbz'):
            shutil.rmtree(f'{path}{track}')
            continue
        old_szs = fnmatch.filter(os.listdir(f'{PATH}{track}/'), '*.szs')[0]
        new_szs = fnmatch.filter(os.listdir(f'{path}{track}/'), '*.szs')[0]
        if await wszst.compare(f'{PATH}{track}/{old_szs}', f'{path}{track}/{new_szs}'):
            print('SZS files are identical.')
            shutil.rmtree(f'{path}{track}')
            continue
        await wkmpt.encode(f'{path}{track}/{new_szs}', f'{path}{track}/course.kmp')
        await wkclt.encode(f'{path}{track}/{new_szs}', f'{path}{track}/course.kcl')
    print('Done.')


if __name__ == '__main__':
    asyncio.run(main())
