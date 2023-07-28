from __future__ import annotations

import gspread
import requests
from gspread.utils import finditem
from oauth2client.service_account import ServiceAccountCredentials


class Spreadsheet(gspread.Spreadsheet):

    def __init__(self, key: str, token_path: str):
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(token_path, scope)
        client = gspread.authorize(creds)
        super().__init__(client, {"id": key})

        self.pages = []
        for page in self.worksheets():
            self.pages.append(SpreadsheetPage(self, page.title))

    def __getitem__(self, item):
        return self.pages[item]

    def refresh_all(self):
        for page in self:
            page.refresh_data()

    def batch_cut_paste(self, ops: list[tuple[Cell, tuple[int, int], Cell]]):
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

        self.batch_update(body=body)
        # self.refresh_all()


class SpreadsheetPage(gspread.Worksheet):

    def __init__(self, parent: Spreadsheet, title: str):
        self.data = []
        self.rawdata = []
        self.parent = parent
        sheet_data = parent.fetch_sheet_metadata()
        try:
            item = finditem(
                lambda x: x["properties"]["title"] == title,
                sheet_data["sheets"],
            )
            super().__init__(parent, item["properties"])
        except (StopIteration, KeyError):
            raise gspread.WorksheetNotFound(title)

        self.data_range = 'A1:' + gspread.utils.rowcol_to_a1(self.row_count, self.col_count)
        self.refresh_data()

    @property
    def row_names(self):
        return [s[0].value for s in self.data][1:]

    @property
    def col_names(self):
        return [s.value for s in self.data[1]]

    def refresh_data(self):
        request_header = {"Authorization": "Bearer " + self.parent.client.auth.token}
        request_link = f'https://sheets.googleapis.com/v4/spreadsheets/{self.parent.id}?ranges=' \
                       f'{self.title.replace(" ", "%20")}!{self.data_range}' \
                       f'&fields=sheets(data(rowData(values(formattedValue,hyperlink))))'
        self.rawdata = [{}]+requests.get(request_link, headers=request_header).json()['sheets'][0]['data'][0]['rowData']
        for row, row_cells in enumerate(self.rawdata):
            row_cells.setdefault('values', [{}])
            row_data = []
            for col, cell in enumerate(row_cells['values']):
                value = cell['formattedValue'] if 'formattedValue' in cell else ''
                link = cell['hyperlink'] if 'hyperlink' in cell else None
                row_data += [Cell(self, row, col, value, link)]
            self.data += [row_data]

    def __getitem__(self, row: str|int|slice):
        if isinstance(row, str):
            row = self.row_names.index(row) + 1
        return self.data[row]

    def read_row(self, row: str|int):
        return [c.value for c in self[row]]

    def read_col(self, col: str|int):
        if isinstance(col, str):
            col = self.col_names.index(col)
        return [c[col].value for c in self[2:]]

    def read_cell(self, row: str|int, col: str|int):
        if isinstance(col, str):
            col = self.col_names.index(col)
        return self.read_row(row)[col]

    def get_row(self, col: str|int, value: str):
        return self.read_col(col).index(value) + 2

    def get_row_name(self, col: str|int, value: str):
        return self.row_names[self.get_row(col, value) - 1]

    def dummy_cell(self, r=0, c=0, value='', link=None):
        return Cell(self, r, c, value, link)


class Cell(str):

    def __new__(cls, page: SpreadsheetPage, r: int, c: int, value='', link=None):
        instance = super().__new__(cls, value)
        return instance

    def __init__(self, page: SpreadsheetPage, r: int, c: int, value='', link=None):
        self.page = page
        self.row = r
        self.col = c
        self.value = value
        self.link = link

    def __repr__(self):
        return self.value
