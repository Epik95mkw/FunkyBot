import os
from typing import Optional

from enum import Enum, auto
from difflib import get_close_matches

from utils import paths
from api import data as d


class Category(Enum):
    CTGP = auto()
    REG = auto()
    UNKNOWN = auto()


# TODO: Make this not ass
class TrackData:
    name: str
    category: Category
    path: str
    sheetdata: Optional[SheetData]
    filedata: Optional[FileData]

    @staticmethod
    def from_spreadsheet():
        test = TrackData()

    @staticmethod
    def from_file():
        pass

    def __str__(self):
        return self.name

    def kmp(self):
        return self.path + self.file[0:-4] + '.kmp'

    def kcl(self):
        return self.path + self.file[0:-4] + '.kcl'

    def txt(self):
        return self.path + self.file[0:-4] + '.txt'

    def set_temp(self):
        self.path = paths.TEMP

    # TODO: remove this
    async def initialize(self, ctx, tl, args, settings: dict):
        # if attachment is allowed & given
        atts = ctx.message.attachments
        if settings['atts'] and atts:
            self.file = atts[0].filename
            self.att_type = self.file[-4:]
            if self.att_type not in settings['atts']:
                await ctx.send('Attached file must be ' + ' or '.join(settings['atts']))
                return
            else:
                self.category = 'att'
                self.path = paths.TEMP
                if len(os.listdir(self.path)) > 0:
                    for f in os.listdir(self.path):
                        os.remove(self.path + f)
                self.s = await ctx.send('Generating...')
                await atts[0].save(fp=self.path + self.file)

        elif atts:
            await ctx.send('Command does not accept attachments.')
            return

        # if track name is given
        elif len(args) > 0:
            self.s = await ctx.send('Searching...')
            track_in = ' '.join(args).upper().strip()
            track_out = tl.search(track_in)

            if not track_out:
                await self.s.edit(content='Track name not recognized.')
                return
            self.name = track_out
            track_out = track_out.replace(':', '')

            if self.name in tl.ctgp:
                if settings['ctgp']:
                    self.category = 'ctgp'
                    self.path = f'{paths.CTGP}{track_out}/'
                else:
                    await self.s.edit(content='Command unavailable for CTGP tracks.')
                    return
            elif self.name in tl.regs:
                if settings['regs']:
                    self.category = 'regs'
                    self.path = f'{paths.REGS}{track_out}/'
                else:
                    await self.s.edit(content='Command unavailable for regular tracks.')
                    return

        # No input, send help message
        else:
            self.s = await ctx.send(content=settings['help'])
            return

        self.success = True


# TODO: Should store fully initialized TrackData objects, not just names
class TrackList:

    def __init__(self, ctgp: list[str], regs: list[str]):
        self.ctgp = ctgp
        self.regs = regs
        self.all = ctgp + regs

    def __getitem__(self, i: int):
        return self.all[i]

    def index(self, string: str):
        return self.all.index(string)

    def upper(self):
        return [t.upper() for t in self.all]

    def abbrev(self):
        return [''.join([c for c in t if c.isupper() or c.isnumeric()]) for t in self.all]

    def first(self):
        return [t.split()[0].upper() if len(t.split()) > 0 else '' for t in self.all]


    def search(self, track_in: str) -> TrackData:
        """ Takes a string input and returns the closest matching track name, or None if no matches. """
        # Step 1: Looks for explicit alias
        if track_in in d.aliases:
            return d.aliases[track_in]

        # Step 2: Looks for full track name, autocorrects slightly
        matches = get_close_matches(track_in, self.upper(), 1, 0.85)
        if len(matches) != 0:
            return self[self.upper().index(str(matches[0]))]

        # Step 3: Looks for abbreviations
        abbrev = track_in.replace(' ', '')
        if abbrev in self.abbrev():
            return self[self.abbrev().index(abbrev)]

        # Step 4: I can't remember what this does
        for n in range(2):
            mlist = []
            ilist = []
            num_words = len(track_in.split())
            for t in self.upper():
                if len(t.split()[n:]) >= num_words and (n == 0 or t.split()[0] in d.prefixes):
                    mlist.append(' '.join(t.split()[n:num_words + n]))
                    ilist.append(self.upper().index(t))

            fmatches = get_close_matches(track_in.upper(), mlist, 3, 0.8)
            if 0 < len(fmatches) < 3:
                return self[ilist[mlist.index(str(fmatches[0]))]]


    def handle_input(self, *, filetypes: tuple, extra_args: tuple = ()):
        """ Decorator that parses user input and calls the command with custom arguments """
        def decorator(cmd):
            async def wrapper(ctx, *args):
                track = None

                file = None
                if ctx.message.attachments:
                    file = ctx.message.attachments[0]
                track_input = (a for a in args if a not in extra_args)
                extra_input = (a for a in args if a in extra_args)

                # handle text input
                if track_input:
                    response = await ctx.send('Searching...')
                    track_name = ' '.join(track_input).upper().strip()
                    track = self.search(track_name)
                    if track is None:
                        await response.edit(content='Track name not recognized.')
                        return None

                # handle file input
                elif file is not None:
                    if not filetypes:
                        await ctx.send('Command does not accept attachments.')
                        return None
                    if (ext := file.filename.split('.')[-1]) not in filetypes:
                        await ctx.send(f'Command does not accept .{ext} files.')
                        return None

                # No input, send help message
                else:
                    if cmd.help:
                        await ctx.send(cmd.help)
                    return None

                if track is None:
                    return None
                return await cmd(ctx, track, extra_input)

            return wrapper
        return decorator
