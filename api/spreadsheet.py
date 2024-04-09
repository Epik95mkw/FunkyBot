from typing import Optional

import gspread
from attr import dataclass
from oauth2client.service_account import ServiceAccountCredentials


BASE_URL = 'https://sheets.googleapis.com/v4/spreadsheets'
REQ_FIELDS = 'sheets(data(rowData(values(formattedValue,hyperlink))))'
SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']


@dataclass(kw_only=True)
class Cell:
    page: int
    row: int
    col: int


class BatchOperation:
    def __init__(self):
        self._operations = []

    def json(self) -> dict:
        return {'requests': self._operations}


    def cut_paste(self, src_start: Cell, src_end: Cell, dest: Cell):
        self._operations.append({
            "cutPaste": {
                "source": {
                    "sheetId": src_start.page,
                    "startRowIndex": src_start.row - 1,
                    "endRowIndex": src_end.row - 1,
                    "startColumnIndex": src_start.col,
                    "endColumnIndex": src_end.col
                },
                "destination": {
                    "sheetId": dest.page,
                    "rowIndex": dest.row - 1,
                    "columnIndex": dest.col
                },
                "pasteType": "PASTE_NORMAL",
            }
        })


class SheetClient:
    client: gspread.Client = None
    sheet_id: str = None

    def __init__(self, sheet_id: str):
        self.sheet_id = sheet_id

    def authorize(self, token_path: str):
        creds = ServiceAccountCredentials.from_json_keyfile_name(token_path, SCOPES)
        self.client = gspread.authorize(creds)

    @property
    def public_url(self) -> str:
        return f'https://docs.google.com/spreadsheets/d/{self.sheet_id}'


    def get_all(self) -> Optional[dict]:
        try:
            res = self.client.request('get', f'{BASE_URL}/{self.sheet_id}?fields={REQ_FIELDS}')
        except gspread.exceptions.APIError as err:
            res = err.response
            print(f'Failed to fetch google sheets data (response code {res.status_code}: {res.reason})')
            return None
        return res.json()


    def get_all_formatted(self) -> Optional[list]:
        out = []
        data = self.get_all()
        if data is None:
            return None

        for sheet in data['sheets']:
            rowlist = []
            maxwidth = max(len(row.setdefault('values', [])) for row in sheet['data'][0]['rowData'])
            for row in sheet['data'][0]['rowData']:
                valuelist = []
                for i in range(maxwidth):
                    if i < len(row['values']):
                        valuelist.append({
                            'value': row['values'][i].setdefault('formattedValue', None),
                            'link':  row['values'][i].setdefault('hyperlink', None)
                        })
                    else:
                        valuelist.append({'value': None, 'link': None})
                rowlist.append(valuelist)
            out.append(rowlist)
        return out


    def batch_update(self, batch: BatchOperation) -> bool:
        try:
            self.client.request('post', f'{BASE_URL}/{self.sheet_id}:batchUpdate', json=batch.json())
            return True
        except gspread.exceptions.APIError as err:
            res = err.response
            print(f'Google Sheets batch update failed (response code {res.status_code}: {res.reason})')
            return False
