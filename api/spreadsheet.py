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


class Spreadsheet(gspread.Spreadsheet):

    def __init__(self, key: str, token_path: str):
        creds = ServiceAccountCredentials.from_json_keyfile_name(token_path, SCOPES)
        client = gspread.authorize(creds)
        super().__init__(client, {'id': key})
        self.pages = self.worksheets()
        self.batch_operations = {'requests': []}

    def __getitem__(self, item) -> gspread.Worksheet:
        return self.pages[item]

    @property
    def sheet_id(self) -> str:
        return self.id

    @property
    def public_url(self) -> str:
        return self.url

    def get_all(self) -> dict:
        return self.fetch_sheet_metadata(params={'fields': REQ_FIELDS})

    def get_all_formatted(self) -> Optional[list]:
        out = []
        data = self.get_all()

        for sheet in data['sheets']:
            rowlist = []
            maxwidth = max(len(row.setdefault('values', [])) for row in sheet['data'][0]['rowData'])
            for row in sheet['data'][0]['rowData']:
                valuelist = []
                for i in range(maxwidth):
                    if i < len(row['values']):
                        valuelist.append({
                            'value': row['values'][i].setdefault('formattedValue', None),
                            'link': row['values'][i].setdefault('hyperlink', None)
                        })
                    else:
                        valuelist.append({'value': None, 'link': None})
                rowlist.append(valuelist)
            out.append(rowlist)
        return out

    def batch_update(self, body):
        print('batch_update called')
        self.batch_operations['requests'].extend(body['requests'])

    def commit_batch_update(self):
        try:
            self.client.request('post', f'{BASE_URL}/{self.sheet_id}:batchUpdate', json=self.batch_operations)
            return True
        except gspread.exceptions.APIError as err:
            res = err.response
            print(f'Google Sheets batch update failed (response code {res.status_code}: {res.reason})')
            return False

    def cut_paste(self, start: Cell, size: tuple[int, int], dest: Cell):
        self.batch_operations["requests"].append({
            "cutPaste": {
                "source": {
                    "sheetId": start.page,
                    "startRowIndex": start.row - 1,
                    "endRowIndex": start.row + size[0] - 1,
                    "startColumnIndex": start.col,
                    "endColumnIndex": start.col + size[1]
                },
                "destination": {
                    "sheetId": dest.page,
                    "rowIndex": dest.row - 1,
                    "columnIndex": dest.col
                },
                "pasteType": "PASTE_NORMAL",
            }
        })
