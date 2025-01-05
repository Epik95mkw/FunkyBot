from api.spreadsheet import Spreadsheet

class CTGPSheet:
    _spreadsheet: Spreadsheet
    _rawdata: list[list[dict]]
    _headers: dict
    _tracknames: dict

    def __init__(self, spreadsheet: Spreadsheet):
        self._spreadsheet = spreadsheet
        self._rawdata = spreadsheet.get_all_formatted()[0]
        self._headers = {cell['value']: i for i, cell in enumerate(self._rawdata[0])}
        self._tracknames = {row[0]['value']: i for i, row in enumerate(self._rawdata[1:], start=1)}

    def __getitem__(self, item):
        if isinstance(item, str):
            return self._rawdata[self._tracknames[item]]
        else:
            return self._rawdata[item]

    @property
    def headers(self) -> list:
        return list(self._headers.keys())

    @property
    def track_names(self) -> list:
        return list(self._tracknames.keys())

    @property
    def sheet_id(self) -> str:
        return self._spreadsheet.sheet_id

    @property
    def public_url(self) -> str:
        return self._spreadsheet.public_url


def test():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    SHEET_ID = os.getenv('SHEET_ID')

    spreadsheet = Spreadsheet(SHEET_ID, '../token.json')
    ctgpsheet = CTGPSheet(spreadsheet)
    print(ctgpsheet._headers)
    print(ctgpsheet._tracknames)

if __name__ == '__main__':
    test()
