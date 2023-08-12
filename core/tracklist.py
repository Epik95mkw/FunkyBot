import os
from typing import Optional, Union
from attr import dataclass
from enum import Enum, auto
import fnmatch
from difflib import get_close_matches

from core import paths
from utils.kmpreader import CheckpointData
from utils.map import Map


class Category(Enum):
    CTGP = auto()
    REG = auto()
    UNKNOWN = auto()


@dataclass
class SheetData:
    wiki_url: str
    version: str
    breakability: str
    rta_status: str
    rta_link: str
    tas_status: str
    tas_link: str
    fullname: str
    creators: str
    slot: str
    wiimm_id: str
    sha1: str
    cpdata: CheckpointData

    @property
    def archive_url(self):
        if self is not None and self.wiimm_id is not None:
            return f'<https://ct.wiimm.de/i/{self.wiimm_id}>'


class TrackData:
    name: str
    category: Category
    path: str
    slot: Optional[str]
    sha1: Optional[str]
    aliases: list
    sheetdata: Optional[SheetData]

    @staticmethod
    def from_spreadsheet(name: str, sheetdata: SheetData):
        track = TrackData()
        track.name = name
        track.category = Category.CTGP
        track.path = paths.CTGP + name.replace(':', '') + '/'
        track.sheetdata = sheetdata
        track.slot = sheetdata.slot
        track.sha1 = sheetdata.sha1
        return track

    @staticmethod
    def from_regdata(regdata: dict):
        track = TrackData()
        track.name = regdata['name']
        track.category = Category.REG
        track.path = paths.REGS + regdata['name'] + '/'
        track.sheetdata = None
        track.slot = regdata['slot']
        track.sha1 = regdata['sha1']
        return track

    @staticmethod
    async def from_file(file):
        track = TrackData()
        track.name = 'Attached Track'
        track.category = Category.UNKNOWN
        track.path = paths.TEMP
        track.sheetdata = None
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

    def szs_path(self) -> Optional[str]:
        files = fnmatch.filter(os.listdir(self.path), '*.szs')
        return None if not files else self.path + files[0]

    def kmp_path(self) -> Optional[str]:
        file = self.path + 'course.kmp'
        return None if not os.path.isfile(file) else file

    def kcl_path(self) -> Optional[str]:
        file = self.path + 'course.kcl'
        return None if not os.path.isfile(file) else file

    def has_file(self, filename) -> bool:
        return filename in os.listdir(self.path)

    def not_yet_broken(self) -> bool:
        return (
            self.sheetdata is not None and
            'Unbreakable' not in self.sheetdata.breakability and
            self.sheetdata.rta_status in ('Not Glitched', 'Lap 4 Bug', 'NLC Glitch') and
            self.sheetdata.tas_status is None
        )

    def is_cleaned(self) -> bool:
        cleaned = [
            'Castle Of Time',
            'Dawn Township',
            'Incendia Castle',
            'Mushroom Peaks',
            'Six King Labyrinth',
        ]
        return self.name in cleaned

    def set_temp(self):
        self.path = paths.TEMP


# TODO: Should store fully initialized TrackData objects, not just names
class TrackList:

    def __init__(self, sheet: list, regs: Map):
        self.data = {}
        self.aliases = dict(zip([s.upper() for s in regs.list('alias')], regs.list('name')))

        for row1, row2 in zip(sheet[0][1:], sheet[1][1:]):
            trackname = row1[0]['value']
            sheetdata = SheetData(
                wiki_url=     row1[0]['link'],
                version=      row1[1]['value'],
                breakability= convert_glitch_status(row1[2]['value']),
                rta_status=   convert_glitch_status(row1[3]['value']),
                rta_link=     row1[3]['link'],
                tas_status=   convert_glitch_status(row1[4]['value']),
                tas_link=     row1[4]['link'],
                fullname=     row2[1]['value'],
                creators=     row2[2]['value'],
                slot=         row2[3]['value'].split()[0],
                wiimm_id=     row2[4]['value'],
                sha1=         row2[5]['value'],
                cpdata= CheckpointData(
                    group_count=   int(row2[6]['value']),
                    cp_count=      int(row2[7]['value']),
                    kcp_count=     int(row2[8]['value']),
                    last_kcp=      int(row2[9]['value']),
                    from_cp0=    float(row2[10]['value']),
                    from_cp1=    float(row2[11]['value']),
                    last_kcp_p=  float(row2[12]['value']),
                    max_ultra_p= float(row2[13]['value']),
                    anomalies=         row2[14]['value']
                )
            )
            self.data.setdefault(trackname.upper(), TrackData.from_spreadsheet(trackname, sheetdata))

        for name in regs.list('name'):
            self.data.setdefault(name.upper(), TrackData.from_regdata(regs.get(name)))


    def __getitem__(self, key: Union[int, str]) -> TrackData:
        if isinstance(key, str):
            return self.data[key.upper()]
        elif isinstance(key, int):
            return list(self.data.values())[key]
        else:
            raise TypeError(f'Invalid key type for TrackList: {type(key)}')

    @property
    def names(self) -> list:
        return [t.name for t in self]

    def index(self, string: str):
        return self.names.index(string)

    def upper(self):
        return [t.upper() for t in self.names]

    def abbrev(self):
        return [''.join([c for c in t if c.isupper() or c.isnumeric()]) for t in self.names]

    def first(self):
        return [t.split()[0].upper() if len(t.split()) > 0 else '' for t in self.names]


    def handle_input(self, *, regs: bool, filetypes: tuple, extra_args: tuple = ()):
        """ Decorator that parses user input and calls the decorated command with custom arguments """
        def decorator(cmd):
            async def wrapper(ctx, *args):
                file = None
                if ctx.message.attachments:
                    file = ctx.message.attachments[0]
                track_input = [a for a in args if a not in extra_args]
                extra_input = [a for a in args if a in extra_args]

                # handle TrackData object input (for internally calling commands)
                if track_input and isinstance(track_input[0], TrackData):
                    track = track_input[0]
                    response = None

                # handle text input
                elif track_input:
                    response = await ctx.send('Searching...')
                    track_name = ' '.join(track_input).upper().strip()
                    track = self.search(track_name)
                    if track is None:
                        await response.edit(content='Track name not recognized.')
                        return
                    if not regs and track.category == Category.REG:
                        await response.edit(content='Command unavailable for regular tracks.')
                        return

                # handle file input
                elif file is not None:
                    if not filetypes:
                        await ctx.send('Command does not accept attachments.')
                        return
                    if (ext := file.filename.split('.')[-1]) not in filetypes:
                        await ctx.send(f'Command does not accept .{ext} files.')
                        return
                    response = await ctx.send('Generating...')
                    track = await TrackData.from_file(file)

                # No input, send help message
                else:
                    if cmd.__doc__:
                        await ctx.send(cmd.__doc__.strip())
                    return

                if track is not None:
                    await cmd(ctx, track, *extra_input)

                if response is not None:
                    await response.delete()

            wrapper.__name__ = cmd.__name__
            wrapper.__doc__ = cmd.__doc__
            return wrapper
        return decorator


    def search(self, track_in: str) -> TrackData:
        """ Takes a string input and returns the closest matching track name, or None if no matches. """
        # Step 1: Look for explicit alias
        if track_in in self.aliases:
            return self[self.aliases[track_in]]

        # Step 2: Looks for full track name, autocorrects slightly
        matches = get_close_matches(track_in, self.upper(), 1, 0.85)
        if len(matches) != 0:
            return self[str(matches[0])]

        # Step 3: Looks for abbreviations
        abbrev = track_in.replace(' ', '')
        if abbrev in self.abbrev():
            return self[self.abbrev().index(abbrev)]

        # Step 4: I can't remember what this does
        prefixes = ['SNES', 'GBA', 'N64', 'GCN', 'DS', 'CTR', 'DKR', 'GP', 'SADX']
        for n in range(2):
            mlist = []
            ilist = []
            num_words = len(track_in.split())
            for t in self.upper():
                if len(t.split()[n:]) >= num_words and (n == 0 or t.split()[0] in prefixes):
                    mlist.append(' '.join(t.split()[n:num_words + n]))
                    ilist.append(self.upper().index(t))

            fmatches = get_close_matches(track_in.upper(), mlist, 3, 0.8)
            if 0 < len(fmatches) < 3:
                return self[ilist[mlist.index(str(fmatches[0]))]]


GLITCH_STATUS = {
    'Yes': 'Unbreakable (Last CP is KCP)',
    'Yes*': 'Unbreakable (95% Rule)',
    'Yes**': 'Unbreakable (Last KCP isn\'t loaded)',
    'Glitched': '150cc RTA',
    '200cc Only': '200cc RTA',
    'Flap Only': '150cc Flap RTA',
    '200cc Flap': '200cc Flap RTA',
    'Slower than NG': '150cc RTA (Slower than No Glitch)',
    '200cc Slower': '200cc RTA (Slower than No Glitch)',
    'NLC Glitch': '150cc No Lap Count Glitch',
    '200cc NLC': '200cc No Lap Count Glitch',
    'TASed': '150cc TASed',
    'TASed Faster than NG': '150cc TASed (Faster than No Glitch)',
    'Flap TASed': '150cc Flap TASed',
}


def convert_glitch_status(key) -> str:
    return key if key not in GLITCH_STATUS else GLITCH_STATUS[key]
