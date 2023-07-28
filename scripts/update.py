import os
import shutil
import requests
from dotenv import load_dotenv

from api import data
from api.spreadsheet import Spreadsheet
from utils import paths, kmp, wiimms

CT_COUNT = 218
SHEET_RANGE = ('A2:G219', 'A2:P219', None)
PATH = paths.CTGP
ALIAS = {
    'N.I.S.W.O.E. Desert': 'NISWOE Desert',
}


def alias(name):
    if name in ALIAS:
        name = ALIAS[name]
    return name


def ctgp_update(sheet: Spreadsheet, archive_info=True):
    #  BEFORE RUNNING:
    #  - Put new track folders into /CTGP Tracks/_UPDATE

    print('CTGP Update')
    old_sha1s = sheet[1].read_col('SHA1')
    new_sha1s = []
    removed_tracks = []
    added_tracks = []

    new_count = input('Number of new tracks? ')
    try:
        new_count = int(new_count)
        assert 0 < new_count <= CT_COUNT
    except (ValueError, AssertionError):
        raise ValueError(f'Enter integer between 1 and {CT_COUNT}.')

    print('Fetching information from Chadsoft...')
    lbs = openurl('https://tt.chadsoft.co.uk/ctgp-leaderboards.json', 'utf-8-sig').json()
    last = ''

    for t in lbs['leaderboards']:
        sha1 = t['trackId']
        if last == sha1:
            continue
        new_sha1s += [sha1]
        if sha1 not in old_sha1s:
            added_tracks += [t]
        last = sha1
    if len(old_sha1s) != CT_COUNT or len(new_sha1s) != CT_COUNT:
        raise IndexError(f'Unexpected number of total tracks\n{CT_COUNT=}\n{len(old_sha1s)=}\n{len(new_sha1s)=}')

    for sha1 in old_sha1s:
        if sha1 not in new_sha1s:
            removed_tracks += [sheet[1].get_row_name('SHA1', sha1)]
    if len(removed_tracks) != new_count or len(added_tracks) != new_count:
        raise IndexError(f'Unexpected number of new tracks\n{new_count=}\n{len(removed_tracks)=}\n{len(added_tracks)=}')

    # Check update directory
    if not os.path.isdir(PATH + '_UPDATE'):
        raise NotADirectoryError('Update directory does not exist.')
    elif not len(os.listdir(PATH + '_UPDATE')) == new_count:
        raise IndexError(f'Unexpected number of directories in _UPDATE: {len(os.listdir(PATH + "_UPDATE"))}')

    for i, d in enumerate(os.listdir(PATH + '_UPDATE')):
        name = alias(added_tracks[i]['name']).replace(':', '')
        if d != name:
            raise ValueError(f'Track names do not match: {name} != {d}')
        elif 'course.kmp' not in os.listdir(PATH + '_UPDATE/' + d):
            raise FileNotFoundError(f'course.kmp not found in {d}/')

    if not os.path.isdir(PATH + '_REMOVED'):
        os.mkdir(PATH + '_REMOVED')

    print('%-30s%-30s' % ('\nAdded tracks:', ' Removed tracks:'))
    for i in range(new_count):
        print('%-30s%-30s' % (alias(added_tracks[i]['name']), removed_tracks[i]))

    yesno: str = input('\nContinue? (Y/N) ')
    if yesno.upper() != 'Y':
        print('\nUpdate aborted.')
        return
    print('')

    # Move old track rows to Removed
    paste_dest = len(sheet[2].row_names) + 3
    rm_rows = []

    sheet[0].format(f'A2:B{CT_COUNT + 1}', {
        'backgroundColor': {
          'red': 1.0,
          'green': 1.0,
          'blue': 1.0
        }})

    sheet[1].add_rows(new_count)
    sheet[2].add_rows(new_count + 2)

    for name in removed_tracks:
        print(f'Removing {name}...')
        rm_rows += [(
            sheet[0][name][0],
            (1, 7),
            sheet[2].dummy_cell(paste_dest, 0)
        )]
        paste_dest += 1

    sheet.batch_cut_paste(rm_rows)
    
    for name in removed_tracks[::-1]:
        sheet[1].delete_rows(sheet[1].get_row('Track', name))

    sheet[0].sort((1, 'asc'), range=SHEET_RANGE[0])

    # Build & add new track rows
    s0 = []
    s1 = []
    for t in added_tracks:
        print(f'Adding {t["name"]}...')
        fullname = ''
        wid = ''
        slotid = str(t['_links']['item']['href'])[13:15]
        slot = f'{slotid} ({data.regs.get(slotid)["alias"]})'

        if archive_info:
            fullname, wid = get_archive_info(t['trackId'])

        with open(PATH + '_UPDATE/' + alias(t['name']).replace(':', '') + '/course.kmp', 'rb') as f:
            kmpobj = kmp.parse(f)
        values = wiimms.calculate_cpinfo(kmpobj, t['name'])

        s0.append([alias(t['name']), t['version']])
        s1.append([alias(t['name']), fullname, ', '.join(t['authors']), slot, wid, t['trackId']] + values + ['', '-'])

    sheet[0].update(f'A{CT_COUNT + 2 - new_count}:B{CT_COUNT + 1}', s0)
    sheet[1].update(f'A{CT_COUNT + 2 - new_count}:P{CT_COUNT + 1}', s1)

    sheet[0].format(f'A{CT_COUNT + 2 - new_count}:B{CT_COUNT + 1}', {
        'backgroundColor': {
            'red': 0.92,
            'green': 1.0,
            'blue': 0.89
        }})

    sheet[0].sort((1, 'asc'), range=SHEET_RANGE[0])
    sheet[1].sort((1, 'asc'), range=SHEET_RANGE[1])

    # Update track directories
    print('Updating directories...')
    for name in removed_tracks:
        name = name.replace(':', '')
        shutil.move(f'{PATH}{name}/', f'{PATH}_REMOVED/{name}/')

    for t in added_tracks:
        name = t['name'].replace(':', '')
        shutil.move(f'{PATH}_UPDATE/{name}/', f'{PATH}{name}/')

    print('\nUpdate complete.')


def get_archive_info(sha1):
    html = openurl(f'https://ct.wiimm.de/i/{sha1}', 'utf-8').text
    hlist = html.split('\n')
    try:
        table = hlist.index('<table class=table-info>')
        fullname = hlist[table + 1][42:-10]
        wid = int(''.join([c for c in hlist[table + 2][45:] if c.isnumeric()]))
    except ValueError:
        fullname = '[track archive not found]'
        wid = '--'

    return fullname, wid


def openurl(url: str, encoding: str) -> requests.Response:
    response = requests.get(url)
    if not response.ok:
        raise ConnectionError(f'Error connecting to host: {url}\nStatus code {response.status_code}')

    response.encoding = encoding
    return response


if __name__ == '__main__':
    load_dotenv()
    s = Spreadsheet(os.getenv('SHEETS_KEY'), '../token.json')
    ctgp_update(s)
