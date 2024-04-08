import gspread
from oauth2client.service_account import ServiceAccountCredentials


BASE_URL = 'https://sheets.googleapis.com/v4/spreadsheets'
REQ_FIELDS = 'sheets(data(rowData(values(formattedValue,hyperlink))))'
SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']


class SheetArea:
    def __init__(self, title: str, data_range: str):
        self.title = title
        self.data_range = data_range

    @property
    def formatted_name(self):
        return self.title.replace(' ', '%20')

    def as_param(self):
        return f'{self.formatted_name}!{self.data_range}'


class SheetClient:
    client: gspread.Client = None
    sheet_id: str = None

    def __init__(self, sheet_id: str):
        self.sheet_id = sheet_id


    def authorize(self, token_path: str):
        creds = ServiceAccountCredentials.from_json_keyfile_name(token_path, SCOPES)
        self.client = gspread.authorize(creds)


    def get_all(self):
        res = self.client.request('get', f'{BASE_URL}/{self.sheet_id}?fields={REQ_FIELDS}')
        if not res.ok:
            print(f'Failed to fetch google sheets data (response code {res.status_code}: {res.reason})')
            return False
        return res.json()


    def get_all_formatted(self):
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
                            'link':  row['values'][i].setdefault('hyperlink', None)
                        })
                    else:
                        valuelist.append({'value': None, 'link': None})
                rowlist.append(valuelist)
            out.append(rowlist)
        return out


    @property
    def public_url(self):
        return f'https://docs.google.com/spreadsheets/d/{self.sheet_id}'


    def batch_cut_paste(self, ops):
        body = {"requests": []}
        for op in ops:
            start, size, dest = op

            body["requests"].append({
                "cutPaste": {
                    "source": {
                        "sheetId": start.page.id,
                        "startRowIndex": start.row - 1,
                        "endRowIndex": start.row + size[0] - 1,
                        "startColumnIndex": start.col,
                        "endColumnIndex": start.col + size[1]
                    },
                    "destination": {
                        "sheetId": dest.page.id,
                        "rowIndex": dest.row - 1,
                        "columnIndex": dest.col
                    },
                    "pasteType": "PASTE_NORMAL",
                }
            })

        self.client.request('post', f'{BASE_URL}/{self.sheet_id}:batchUpdate', json=body)
