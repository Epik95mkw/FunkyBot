import requests
import json
import time
from enum import Enum

API_URL = 'https://tt.chadsoft.co.uk'
GHOST_URL = 'https://chadsoft.co.uk/time-trials'

class Category(Enum):
    NORMAL = 0
    GLITCH = 1
    NO_SC = 2


def _fetch(url: str) -> requests.Response:
    response = requests.get(url)
    if not response.ok:
        raise ConnectionError(f'Error connecting to host: {url}\nStatus code {response.status_code}')
    response.encoding = 'utf-8-sig'
    return response


def all_leaderboards():
    return _fetch(f'{API_URL}/ctgp-leaderboards.json').json()


def get_leaderboard(slot: str, sha1: str, category: Category, is_flap: bool, is_200: bool,
                    *, start: int = 0, limit: int = 100):
    if slot.startswith('0x'):
        slot = slot[2:]
    url = (f'{API_URL}/leaderboard/{slot}/{sha1}/0{category.value + (4 if is_200 else 0)}'
           f'{"-fast-lap" if is_flap else ""}.json?start={start}&limit={limit}')
    try:
        return _fetch(url).json()
    except json.decoder.JSONDecodeError:
        return None


def get_bkt_url(slot: str, sha1: str, category: Category, is_flap: bool, is_200: bool):
    leaderboard = get_leaderboard(slot, sha1, category, is_flap, is_200, start=0, limit=1)
    return GHOST_URL + leaderboard['ghosts'][0]['_links']['item']['href'][0:-4] + 'html'


def _get_all_best_splits():
    out_dir = r'C:/Users/epik9/Desktop/chadsoft_data/raw/'
    start_index = 27
    ghosts_per_track = 30

    leaderboards = all_leaderboards()['leaderboards']
    leaderboards = [track for track in leaderboards if track.setdefault('categoryId', 0) == 0]

    for i, track in enumerate(leaderboards):
        if i < start_index:
            continue

        name = track['name']
        out = {
            'name': name,
            'ghosts': []
        }
        track_url = API_URL + track['_links']['item']['href'] + f'?start=0&limit={ghosts_per_track}'

        print(f'({i}) Loading leaderboard for {name}...')
        lb = _fetch(track_url).json()
        print('Loaded.')

        for j, ghost in enumerate(lb['ghosts'][:ghosts_per_track]):
            ghost_url = API_URL + ghost['_links']['item']['href']
            print(f'    {j + 1}: {ghost_url}')
            ghost_data = _fetch(ghost_url).json()
            out['ghosts'].append(ghost_data)
            time.sleep(1)

        with open(out_dir + name + '.json', 'w') as f:
            f.write(json.dumps(out, indent=4))

        time.sleep(40)


if __name__ == '__main__':
    _get_all_best_splits()
