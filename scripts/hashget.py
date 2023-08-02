import asyncio
import fnmatch
import os
import shutil

import requests
from dotenv import load_dotenv

from api.spreadsheet_old import Spreadsheet
from hashcheck import hash_check
from utils import paths, wiimms as w

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

    for track, sha1 in incorrect[i:]:
        if not os.path.isdir(f'{path}{track}'):
            os.mkdir(f'{path}{track}')
        if not await download_wbz(path + track, sha1, track):
            shutil.rmtree(f'{path}{track}')
            continue
        if not await w.szs_encode(f'{path}{track}/', f'{track}.wbz'):
            shutil.rmtree(f'{path}{track}')
            continue
        old_szs = fnmatch.filter(os.listdir(f'{PATH}{track}/'), '*.szs')[0]
        new_szs = fnmatch.filter(os.listdir(f'{path}{track}/'), '*.szs')[0]
        if await w.szs_cmp(f'{PATH}{track}/{old_szs}', f'{path}{track}/{new_szs}'):
            print('SZS files are identical.')
            shutil.rmtree(f'{path}{track}')
            continue
        await w.wkmpt_encode(f'{path}{track}/', new_szs, 'course.kmp')
        await w.wkclt_encode(f'{path}{track}/', new_szs, 'course.kcl')
    print('Done.')


if __name__ == '__main__':
    asyncio.run(main())
