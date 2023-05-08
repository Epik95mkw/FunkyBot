import os
from difflib import get_close_matches

from . import paths, dicts as d


class TrackList:

    def __init__(self, ctgp: list[str], new: list[str], regs: list[str]):
        self.ctgp = ctgp
        self.new = new
        self.regs = regs
        self.ftl = ctgp + ['NEW ' + t for t in new] + regs

    def __getitem__(self, i: int):
        return self.ftl[i]

    def index(self, string: str):
        return self.ftl.index(string)

    def upper(self):
        return [t.upper() for t in self.ftl]

    def abbrev(self):
        return [''.join([c for c in t if c.isupper() or c.isnumeric()]) for t in self.ftl]

    def first(self):
        return [t.split()[0].upper() if len(t.split()) > 0 else '' for t in self.ftl]


class TrackData:
    name = 'Attached Track'
    file = 'course.xxx'
    path: str
    category: str
    att_type = ''
    s = None
    success = False

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

    async def initialize(self, ctx, tl: TrackList, args, settings: dict):

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
            track_out = findtrack(track_in, tl)

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
            elif self.name in tl.new:
                if settings['new']:
                    self.category = 'new'
                    self.path = f'{paths.CTGP}_UPDATE/{track_out}/'
                else:
                    await self.s.edit(content='Command unavailable for upcoming tracks.')
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


def findtrack(track_in: str, tl: TrackList) -> str:

    # Test 1: Looks for explicit alias
    if track_in in d.aliases:
        return d.aliases[track_in]

    # Test 2: Looks for full track name, autocorrects slightly
    matches = get_close_matches(track_in, tl.upper(), 1, 0.85)
    if len(matches) != 0:
        return tl[tl.upper().index(str(matches[0]))]

    # Test 3: Looks for abbreviations
    abbrev = track_in.replace(' ', '')
    if abbrev in tl.abbrev():
        return tl[tl.abbrev().index(abbrev)]

    # Test 4: I can't remember what this does
    for n in range(2):
        mlist = []
        ilist = []
        num_words = len(track_in.split())
        for t in tl.upper():
            if len(t.split()[n:]) >= num_words and (n == 0 or t.split()[0] in d.prefixes):
                mlist.append(' '.join(t.split()[n:num_words + n]))
                ilist.append(tl.upper().index(t))

        fmatches = get_close_matches(track_in.upper(), mlist, 3, 0.8)
        if 0 < len(fmatches) < 3:
            return tl[ilist[mlist.index(str(fmatches[0]))]]
