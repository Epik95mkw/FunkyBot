import difflib
from typing import Optional

import discord
from core import paths


def parse_track_name(track_in: str, valid_tracks: list[str]) -> Optional[str]:
    """
    Takes a string input and returns the closest matching track name, or None if no matches.

    :param track_in: Arbitrary input string
    :param valid_tracks: List of valid track names to match input string to
    """
    valid_tracks_upper = [s.upper() for s in valid_tracks]

    # Step 1: Looks for full track name, autocorrects slightly
    matches = difflib.get_close_matches(track_in.upper(), valid_tracks_upper, 1, 0.85)
    if matches:
        index = valid_tracks_upper.index(str(matches[0]))
        return valid_tracks[index]

    # Step 2: Looks for abbreviations
    abbrev = track_in.replace(' ', '').upper()
    for t in valid_tracks:
        if abbrev == ''.join([c for c in t if c.isupper() or c.isnumeric()]):
            return t

    # Step 3: Looks for the first part of the name(?)
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

    return None


async def save_to_temp(file: discord.Attachment):
    paths.clear_temp()
    filepath = paths.TEMP / file.filename
    await file.save(filepath)
    return filepath


class EmptyInputError(Exception):
    pass

def help_msg(cmd):
    async def wrapper(ctx, *args):
        async with ctx.typing():
            try:
                await cmd(ctx, *args)
            except EmptyInputError:
                if cmd.__doc__:
                    await ctx.send(cmd.__doc__.strip())

    wrapper.__name__ = cmd.__name__
    wrapper.__doc__ = cmd.__doc__
    return wrapper


if __name__ == '__main__':
    print(parse_track_name('rainbw', ['SNES Rainbow Road']))
