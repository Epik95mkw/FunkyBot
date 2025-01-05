import difflib
import os
from typing import Optional
from enum import Enum, auto

import discord

from api import gamedata
from core import paths
from core.ctgp_sheet import CTGPSheet


class Category(Enum):
    CTGP = auto()
    REG = auto()
    UNKNOWN = auto()


class TrackData:
    name: str
    path: str
    category: Category
    slot = Optional[str]
    sha1 = Optional[str]

    @staticmethod
    def parse_ctgp_name(input_text: str, sheet: CTGPSheet):
        name = _parse_track_name(input_text, sheet.track_names)
        if name is None:
            return None
        track = TrackData()
        track.name = name
        track.category = Category.CTGP
        track.path = paths.CTGP + name.replace(':', '') + '/'
        track.slot = None
        track.sha1 = None
        return track

    @staticmethod
    def parse_reg_name(input_text: str):
        name = _parse_track_name(input_text, gamedata.regs.list('name'))
        if name is None:
            return None
        track = TrackData()
        track.name = regdata['name']
        track.category = Category.REG
        track.path = paths.REGS + regdata['name'] + '/'
        track.slot = regdata['slot']
        track.sha1 = regdata['sha1']
        return track

    @staticmethod
    async def parse_attachments(attachments: list[discord.Attachment]):
        if not attachments:
            return None
        file = attachments[0]
        track = TrackData()
        track.name = 'Attached Track'
        track.category = Category.UNKNOWN
        track.path = paths.TEMP
        track.slot = None
        track.sha1 = None
        paths.clear_temp()
        await file.save(fp=paths.TEMP + file.filename)
        return track

    def __str__(self):
        return self.name

    @property
    def cpdata(self) -> Optional[CheckpointData]:
        if self.sheetdata is not None:
            return self.sheetdata.cpdata

    def set_cpdata(self, data: CheckpointData):
        self.sheetdata.cpdata = data

    def szs_file(self) -> Optional[str]:
        files = fnmatch.filter(os.listdir(self.path), '*.szs')
        return None if not files else self.path + files[0]

    def kmp_file(self) -> Optional[str]:
        file = self.path + 'course.kmp'
        return None if not os.path.isfile(file) else file

    def kcl_file(self) -> Optional[str]:
        file = self.path + 'course.kcl'
        return None if not os.path.isfile(file) else file

    def has_file(self, filename) -> bool:
        return filename in os.listdir(self.path)

    def set_temp(self):
        self.path = paths.TEMP


def _parse_track_name(track_in: str, valid_tracks: list[str]) -> Optional[str]:
    """ Takes a string input and returns the closest matching track name, or None if no matches. """
    valid_tracks_upper = [s.upper() for s in valid_tracks]

    # Step 1: Looks for full track name, autocorrects slightly
    matches = difflib.get_close_matches(track_in, valid_tracks_upper, 1, 0.85)
    if len(matches) != 0:
        return str(matches[0])

    # Step 2: Looks for abbreviations
    abbrev = track_in.replace(' ', '')
    for t in valid_tracks:
        if abbrev == ''.join([c for c in t if c.isupper() or c.isnumeric()]):
            return t

    # Step 3: I can't remember what this does
    prefixes = ['SNES', 'GBA', 'N64', 'GCN', 'DS', 'CTR', 'DKR', 'GP', 'SADX']
    for n in range(2):
        mlist = []
        ilist = []
        num_words = len(track_in.split())
        for i, t in enumerate(valid_tracks_upper):
            if len(t.split()[n:]) >= num_words and (n == 0 or t.split()[0] in prefixes):
                mlist.append(' '.join(t.split()[n:num_words + n]))
                ilist.append(i)

        fmatches = difflib.get_close_matches(track_in.upper(), mlist, 3, 0.8)
        if 0 < len(fmatches) < 3:
            return valid_tracks[ilist[mlist.index(str(fmatches[0]))]]
