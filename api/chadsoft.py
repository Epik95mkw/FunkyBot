import requests
import json

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
