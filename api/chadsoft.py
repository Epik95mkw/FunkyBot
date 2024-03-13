import requests
import json
import time

API_URL = 'https://tt.chadsoft.co.uk'
GHOST_URL = 'https://chadsoft.co.uk/time-trials'


def openurl(url: str, encoding: str) -> requests.Response:
    response = requests.get(url)
    if not response.ok:
        raise ConnectionError(f'Error connecting to host: {url}\nStatus code {response.status_code}')
    response.encoding = encoding
    return response


def all_leaderboards():
    return openurl(API_URL + '/ctgp-leaderboards.json', 'utf-8-sig').json()


def get_leaderboard(slot: str, sha1: str, category: int, is_flap: bool, is_200: bool):
    if is_200:
        category += 4
    url = f'{API_URL}/leaderboard/{slot}/{sha1}/0{category}{"-fast-lap" if is_flap else ""}.json'
    try:
        return openurl(url, 'utf-8-sig').json()
    except json.decoder.JSONDecodeError:
        return None


def get_bkt_url(leaderboard_json):
    return GHOST_URL + leaderboard_json['ghosts'][0]['_links']['item']['href'][0:-4] + 'html'


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
        track_url = API_URL + track['_links']['item']['href']

        print(f'({i}) Loading leaderboard for {name}...')
        lb = openurl(track_url, 'utf-8-sig').json()
        print('Loaded.')

        for j, ghost in enumerate(lb['ghosts'][:ghosts_per_track]):
            ghost_url = API_URL + ghost['_links']['item']['href']
            print(f'    {j + 1}: {ghost_url}')
            ghost_data = openurl(ghost_url, 'utf-8-sig').json()
            out['ghosts'].append(ghost_data)
            time.sleep(1)

        with open(out_dir + name + '.json', 'w') as f:
            f.write(json.dumps(out, indent=4))

        time.sleep(40)


if __name__ == '__main__':
    _get_all_best_splits()
