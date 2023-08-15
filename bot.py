import os
import fnmatch
import random
from datetime import datetime

import discord
from discord.ext.commands import Bot, Command
from dotenv import load_dotenv

from api import spreadsheet, gamedata, chadsoft
from utils import szsreader, kmpreader, gcpfinder
from core import paths, cpinfo
from core.tracklist import TrackList, TrackData

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
SHEET_ID = os.getenv('SHEET_ID')

client = spreadsheet.authorize('./token.json')
tracklist = TrackList(
    sheet=spreadsheet.get_all_formatted(client, SHEET_ID),
    regs=gamedata.regs
)

bot = Bot(command_prefix='\\', help_command=None)


@bot.event
async def on_ready():
    if os.path.isfile('./core/extra.py'):
        bot.load_extension('core.extra')
    await bot.change_presence(activity=discord.Game('\\help for commands'))
    print(f'Connected: {datetime.now().strftime("%m/%d/%Y %H:%M:%S")}')


@bot.event
async def on_command_error(ctx, error):
    if not isinstance(error, discord.ext.commands.errors.CommandNotFound):
        await ctx.send(error)
        raise error.original if hasattr(error, 'original') else error


# COMMANDS #############################################################################################################


@bot.command(name='help')
async def cmd_help(ctx):
    cmdlist = '\n'.join(v.help for v in globals().values() if isinstance(v, Command) and v.help)
    footer = '<track name> accepts any custom track in CTGP. Track names are case insensitive and ' \
             'can be replaced with abbreviations ("dcr", "snes mc2", etc.).'
    embed = discord.Embed(title="Commands:", description=cmdlist[:3000] + '\n\n' + footer, color=0xCA00FF)
    await ctx.send(embed=embed)


@bot.command(name='links')
async def links(ctx):
    """ \\links - Get important CT resources """
    desc = 'CTGP Ultras Spreadsheet:\n' \
        f'{spreadsheet.public_url(SHEET_ID)}\n\n' \
        'CTGP Tockdom Page:\n' \
        'http://wiki.tockdom.com/wiki/CTGPR\n\n' \
        'CTGP Track Files Dropbox:\n' \
        'https://www.dropbox.com/sh/9phl0p4d663fmel/AAD0Xo4JyuYZng3AW4ynb2Nwa?dl=0\n\n' \
        'CTGP Upcoming Track Updates:\n' \
        'https://docs.google.com/spreadsheets/d/1xwhKoyypCWq5tCRTI69ijJoDiaoAVsvYAxz-q4UBNqM/edit?usp=sharing\n\n' \
        'Lorenzi\'s KMP Editor:\n' \
        'https://github.com/hlorenzi/kmp-editor/releases\n\n' \
        'Brawlcrate:\n' \
        'https://github.com/soopercool101/BrawlCrate/releases\n\n' \
        'Download CTools:\n' \
        'http://www.chadsoft.co.uk/ctools/setup/ctoolssetup.msi'
    embed = discord.Embed(title='**Resources:**', description=desc, color=0xCA00FF)
    await ctx.send(embed=embed)


@bot.command(name='spreadsheet')
async def get_sheetlink(ctx):
    """ \\spreadsheet - Get link to CTGP ultras spreadsheet """
    await ctx.send(spreadsheet.public_url(SHEET_ID))


@bot.command(name='info')
@tracklist.handle_input(regs=False, filetypes=())
async def get_info(ctx, track: TrackData):
    """ \\info <track name> - Get general track information """
    sdata = track.sheetdata

    if 'Unbreakable' in sdata.breakability:
        status = sdata.breakability
    elif sdata.tas_status is None:
        status = sdata.rta_status
    elif sdata.rta_status == 'Not Glitched':
        status = sdata.tas_status
    else:
        status = sdata.rta_status + ', ' + sdata.tas_status

    desc = f'Creator(s): {sdata.creators}\n' \
           f'CTGP Version: {sdata.version}\n' \
           f'Track Slot: {sdata.slot}\n' \
           f'CT Archive ID: {sdata.wiimm_id}\n' \
           f'\n' \
           f'Glitch Status: {status}\n' \
           f'\n' \
           f'Wiki Page: <{sdata.wiki_url or "[link not found]"}>\n' \
           f'CT Archive Page: {sdata.archive_url or "N/A"}'
    await ctx.send(embed=discord.Embed(title=track.name, description=desc, color=0xCA00FF))


@bot.command(name='video')
@tracklist.handle_input(regs=False, filetypes=())
async def get_video(ctx, track: TrackData):
    """ \\video <track name> - Get video of track\'s ultra shortcut """
    sdata = track.sheetdata
    await ctx.send(content=f'**{track.name}**')
    if sdata.rta_link is not None:
        await ctx.send(f'{sdata.rta_status}: \n{sdata.rta_link}')
    if sdata.tas_link is not None:
        await ctx.send(f'{sdata.tas_status}: \n{sdata.tas_link}')
    if sdata.rta_link is None and sdata.tas_link is None:
        await ctx.send('There is no video available for this track.')


@bot.command(name='bkt')
@tracklist.handle_input(regs=True, filetypes=(), extra_args=('glitch', 'no-sc', 'flap', '200cc', '200'))
async def get_bkt(ctx, track: TrackData, *args):
    """ \\bkt <track name> [glitch/no-sc] [flap] [200cc] """
    args = [a.lower() for a in args]
    category = 0
    is_flap = ''
    is_200 = False

    # Parse command
    for a in args:
        if a == 'glitch':
            category = 1
        elif a == 'no-sc':
            category = 2
        elif a == 'flap':
            is_flap = True
        elif a == '200cc' or a == '200':
            is_200 = True

    leaderboard = chadsoft.get_leaderboard(track.slot, track.sha1, category, is_flap, is_200)
    bkt_url = chadsoft.get_bkt_url(leaderboard)

    await ctx.send(bkt_url)


@bot.command(name='szs')
@tracklist.handle_input(regs=False, filetypes=())
async def get_szs(ctx, track: TrackData):
    """ \\szs <track name> - Download track\'s szs file """
    title = f'**{track}**'
    if track.is_cleaned():
        title += '\n(Note: Use \kmp to get clean KCL file)'

    file = track.szs_file()
    if file is None:
        raise FileNotFoundError('SZS file not found')
    else:
        await ctx.send(title, file=discord.File(file))


@bot.command(name='kmp')
@tracklist.handle_input(regs=True, filetypes=('szs',))
async def get_kmp(ctx, track: TrackData):
    """ \\kmp <track name> - Download track\'s kmp and kcl files """
    if track.kmp_file() is None:
        szsreader.extract_file_to(track.szs_file(), track.path + 'course.kmp', 'course.kmp')
    if track.kcl_file() is None:
        szsreader.extract_file_to(track.szs_file(), track.path + 'course.kcl', 'course.kcl')

    title = f'**{track.name}**'
    if track.is_cleaned():
        title += '\n(Note: KCL modified to remove invalid triangles)'

    files = [discord.File(track.kmp_file(), filename='course.kmp'),
             discord.File(track.kcl_file(), filename='course.kcl')]
    await ctx.send(f'**{track}**', files=files)


@bot.command(name='img')
@tracklist.handle_input(regs=True, filetypes=())
async def get_cpmap(ctx, track: TrackData):
    """ \\img <track name> - Get image of track\'s checkpoint map """
    files = fnmatch.filter(os.listdir(track.path), '*.png')
    if len(files) != 1:
        raise FileNotFoundError('Image not found')
    await ctx.send(f'**{track}**', file=discord.File(track.path + files[0]))


@bot.command(name='cpinfo')
@tracklist.handle_input(regs=True, filetypes=('szs', 'kmp'))
async def get_cpinfo(ctx, track: TrackData):
    """ \\cpinfo <track name> - Get stats for track\'s checkpoint map """
    cpdata = track.cpdata
    if cpdata is None:    # not on spreadsheet
        if track.kmp_file() is None:
            szsreader.extract_file_to(track.szs_file(), track.path + 'course.kmp', 'course.kmp')
        with open(track.kmp_file(), 'rb') as f:
            rawkmp = kmpreader.parse(f)
        cpdata = cpinfo.calculate_cpinfo(rawkmp, track.name, silent=True)

    if cpdata.from_cp0 == '-1':
        await ctx.send('Checkpoint info unavailable for this track (multiple finish lines).')
        return

    desc = f'Checkpoints: {cpdata.cp_count}\n' \
           f'Checkpoint Groups: {cpdata.group_count}\n' \
           f'Key Checkpoints: {cpdata.kcp_count}\n' \
           f'Last Key Checkpoint: {cpdata.last_kcp}\n' \
           '\n' \
           f'95% from Checkpoint 0: {cpdata.from_cp0}\n' \
           f'95% from Checkpoint 1: {cpdata.from_cp1}\n' \
           'Last Key Checkpoint %: ' + '{:.2f}'.format(float(cpdata.last_kcp_p) * 100) + '%\n' \
           'Maximum % for Ultra: ' + '{:.2f}'.format(float(cpdata.max_ultra_p) * 100) + '%\n' \

    embed = discord.Embed(title=track.name, description=desc, color=0xCA00FF)
    await ctx.send(content='', embed=embed)


@bot.command(name='gcps')
@tracklist.handle_input(regs=True, filetypes=('szs', 'kmp'), extra_args=('sp', 'split-paths', 'nf', 'no-fill'))
async def get_gcps(ctx, track: TrackData, *args):
    """ \\gcps [option] <track name> - Generates Desmos graph of the full track. """
    splitpaths = 'sp' in args or 'split-paths' in args
    noquads = 'nf' in args or 'no-fill' in args

    if track.kmp_file() is None:
        szsreader.extract_file_to(track.szs_file(), track.path + 'course.kmp', 'course.kmp')

    if splitpaths or noquads or f'{track.name}.desmos.html' not in os.listdir(track.path):
        path = paths.TEMP if splitpaths or noquads else track.path

        with open(track.kmp_file(), 'rb') as f:
            rawkmp = kmpreader.parse(f)

        gcplist = gcpfinder.find(rawkmp, bounds=(-500000, 500000))
        html = gcpfinder.graph(rawkmp, gcplist, splitpaths, (not noquads), bounds=(-500000, 500000))

        append = f'{html}\n<!--{", ".join([str(g) for g in gcplist])}-->'
        with open(f'{path}{track.name}.desmos.html', 'w') as out:
            out.write(append)
    else:
        path = track.path
        with open(f'{track.path}{track.name}.desmos.html', 'r') as f:
            gcplist = [s for s in f.read().split('\n')[-1][4:-3].split(', ') if s.isnumeric()]

    if len(gcplist) > 0:
        gcpfound = 'Ghost checkpoints found at: ' + ', '.join([str(g) for g in gcplist])
    else:
        gcpfound = 'No ghost checkpoints found.'

    msg = f'**{track.name}**\n{gcpfound}\nDownload file and open in browser:'
    await ctx.send(content=msg, file=discord.File(f'{path}{track.name}.desmos.html'))


@bot.command(name='random')
async def random_track(ctx, arg=''):
    """ \\random [all] - Get random unbroken track, include 'all' to get any track """
    track = tracklist[int(218*random.random() + 2)]
    if arg.lower() == 'all' or track.not_yet_broken():
        await get_info(ctx, track)
    else:
        await random_track(ctx)


if __name__ == '__main__':
    print(f'Process started: {datetime.now().strftime("%m/%d/%Y %H:%M:%S")}')
    bot.run(DISCORD_TOKEN)
