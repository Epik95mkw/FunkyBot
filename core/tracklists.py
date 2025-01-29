import os
import json
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from abc import ABC, abstractmethod

from core import command_utils
from api.spreadsheet import Spreadsheet


class TrackList(ABC):
    @property
    @abstractmethod
    def _dict(self) -> dict:
        pass

    @abstractmethod
    def refresh(self):
        pass

    def names(self):
        return list(self._dict.keys())

    def search(self, track_in):
        name = command_utils.parse_track_name(track_in, self.names())
        return self._dict[name] if name is not None else None

    def __repr__(self):
        return '\n'.join(f'{k}: {v}' for k, v in self._dict.items())


@dataclass
class FilesystemTrack:
    name: str
    authors: str
    slot: str
    filename: str
    music: str
    sha1: str
    dir: Path

class FilesystemTrackList(TrackList):
    def __init__(self, root_dir: os.PathLike):
        self._root_dir = Path(root_dir)
        self._d = {}
        self.refresh()

    @property
    def _dict(self):
        return self._d

    def search(self, track_in) -> Optional[FilesystemTrack]:
        return super().search(track_in)

    def refresh(self):
        self._d.clear()
        for track in os.listdir(self._root_dir):
            d = self._root_dir / track
            with open(d / 'info.json', 'r') as f:
                info = json.load(f)
            self._d[info['name']] = FilesystemTrack(dir=d, **info)


@dataclass
class SpreadsheetTrack:
    name: str
    version: str
    unbreakable: str
    rta_status: Optional[str]
    tas_status: Optional[str]
    wiki_url: Optional[str]
    rta_video: Optional[str]
    tas_video: Optional[str]

class SpreadsheetTrackList(TrackList):
    def __init__(self, spreadsheet: Spreadsheet):
        self._spreadsheet = spreadsheet
        self._d = {}
        self.refresh()

    @property
    def _dict(self):
        return self._d

    def search(self, track_in) -> Optional[SpreadsheetTrack]:
        return super().search(track_in)

    def refresh(self):
        self._d.clear()
        rawdata = self._spreadsheet.get_all_formatted()[0]
        for row in rawdata[1:]:
            self._d[row[0]['value']] = SpreadsheetTrack(
                name        =row[0]['value'],
                version     =row[1]['value'],
                unbreakable =row[2]['value'],
                rta_status  =row[3]['value'],
                tas_status  =row[4]['value'],
                wiki_url  =row[0]['link'],
                rta_video =row[3]['link'],
                tas_video =row[4]['link'],
            )


# if __name__ == '__main__':
#     from core import paths
#     SHEET_ID = os.getenv('SHEET_ID')
#     fs_tracks = FilesystemTrackList(paths.CTGP)
#     spreadsheet = Spreadsheet(SHEET_ID, '../token.json')
#     sheet_tracks = SpreadsheetTrackList(spreadsheet)
#     print(sheet_tracks)
