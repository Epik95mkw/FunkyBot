import fnmatch
import json
import os
import random
from datetime import datetime

import discord
import requests
from discord.ext.commands import Bot
from dotenv import load_dotenv

import utils.kmp
from api import spreadsheet, gamedata, data as d
from utils import wiimms as w, kmp, paths, gcpfinder
from components.tracklist import TrackList, TrackData, Category

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
SHEET_ID = os.getenv('SHEETS_KEY')

client = spreadsheet.authorize('./token.json')
tracklist = TrackList(
    sheet=spreadsheet.get_formatted(client, SHEET_ID),
    regs=gamedata.regs.list('name')
)


bot = Bot(command_prefix='\\', help_command=None)


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game('\\help for commands'))
    print(f'Connected: {datetime.now().strftime("%m/%d/%Y %H:%M:%S")}')


# TODO: write better error handler
@bot.event
async def on_command_error(ctx, error):
    if not isinstance(error, discord.ext.commands.errors.CommandNotFound):
        await ctx.send(error)
        raise error.original


# COMMANDS #############################################################################################################
# TODO: Move all API stuff to their own modules

@bot.command(name='help')
async def cmd_help(ctx):
    embed = discord.Embed(title="Commands:", description=d.cmdlist, color=0xCA00FF)
    await ctx.send(embed=embed)


@bot.command(name='links')
async def links(ctx):
    desc = f'CTGP Ultras Spreadsheet:\n{spreadsheet.public_url(SHEET_ID)}\n\n{d.links}'
    embed = discord.Embed(title='**Resources:**', description=desc, color=0xCA00FF)
    await ctx.send(embed=embed)


@bot.command(name='spreadsheet')
async def get_sheetlink(ctx):
    await ctx.send(spreadsheet.public_url(SHEET_ID))


@bot.command(name='info')
@tracklist.handle_input(regs=False, filetypes=())
async def info(ctx, track: TrackData):
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
async def vid(ctx, track: TrackData):
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
            is_flap = '-fast-lap'
        elif a == '200cc' or a == '200':
            is_200 = True

    # Build URL & get JSON
    if is_200:
        category += 4
    suffix = f'0{category}{is_flap}'

    if track.category == Category.REG:
        reg = gamedata.regs.get(track.name)
        slot = reg['slot']
        sha1 = reg['sha1']
    else:
        slot = track.sheetdata.slot
        sha1 = track.sheetdata.sha1

    lb_url = f'https://tt.chadsoft.co.uk/leaderboard/{slot}/{sha1}/{suffix}'
    lb_req = requests.get(lb_url + '.json')
    lb_req.encoding = 'utf-8-sig'
    try:
        lb = lb_req.json()
    except json.decoder.JSONDecodeError:
        await ctx.send('Category does not exist.')
        return

    bkt_url = 'https://chadsoft.co.uk/time-trials' + lb['ghosts'][0]['_links']['item']['href'][0:-4] + 'html'
    await ctx.send(bkt_url)


@bot.command(name='szs')
@tracklist.handle_input(regs=False, filetypes=())
async def szs(ctx, track: TrackData):
    """ \\szs <track name> - Download track\'s szs file """
    title = f'**{track}**'
    if track.is_cleaned():
        title += '\n(Note: Use \kmp to get clean KCL file)'

    file = track.szs_path()
    if file is None:
        raise FileNotFoundError('SZS file not found')
    else:
        await ctx.send(title, file=discord.File(file))


@bot.command(name='kmp')
@tracklist.handle_input(regs=True, filetypes=('szs',))
async def get_kmp(ctx, track: TrackData):
    """ \\kmp <track name> - Download track\'s kmp and kcl files """
    if track.kmp_path() is None:
        await w.wkmpt_encode(track.szs_path(), track.path + 'course.kmp')
    if track.kcl_path() is None:
        await w.wkclt_encode(track.szs_path(), track.path + 'course.kcl')

    title = f'**{track.name}**'
    if track.is_cleaned():
        title += '\n(Note: KCL modified to remove invalid triangles)'

    files = [discord.File(track.kmp_path(), filename='course.kmp'),
             discord.File(track.kcl_path(), filename='course.kcl')]
    await ctx.send(f'**{track}**', files=files)


@bot.command(name='kmptext')
@tracklist.handle_input(regs=True, filetypes=('szs', 'kmp'))
async def kmptext(ctx, track: TrackData):
    """ \\kmptext <track name> - Get track kmp in both raw and text form """
    files = []
    if track.kmp_path() is None and track.szs_path() is not None:
        await w.wkmpt_encode(track.szs_path(), track.path + 'course.kmp')
        files += [discord.File(track.kmp_path(), filename='course.kmp')]

    if not track.has_file('kmp.txt') or not track.has_file('kmp_errors.txt'):
        await w.wkmpt_decode(track.kmp_path(), track.path + 'kmp.txt', track.path + 'kmp_errors.txt')
    files += [discord.File(track.path + 'kmp.txt'), discord.File(track.path + 'kmp_errors.txt')]

    await ctx.send(f'**{track.name}**', files=files)


@bot.command(name='kcltext')
@tracklist.handle_input(regs=True, filetypes=('szs', 'kcl'))
async def kcltext(ctx, track: TrackData):
    """ \\kcltext <track name> - Get track kcl in both raw and text form """
    files = []
    if track.kmp_path() is None and track.szs_path() is not None:
        await w.wkclt_encode(track.szs_path(), track.path + 'course.kcl')
        files += [discord.File(track.kcl_path(), filename='course.kcl')]

    if not track.has_file('kcl_flags.txt'):
        await w.wkclt_flags(track.kcl_path(), track.path + 'kcl_flags.txt')
    files += [discord.File(track.path + 'kcl_flags.txt')]

    title = f'**{track.name}**'
    if track.is_cleaned():
        title += '\n(Note: KCL modified to remove invalid triangles)'

    await ctx.send(title, files=files)


@bot.command(name='img')
@tracklist.handle_input(regs=True, filetypes=())
async def cpmap1(ctx, track: TrackData):
    """ \\img <track name> - Get image of track\'s checkpoint map """
    files = fnmatch.filter(os.listdir(track.path), '*.png')
    if len(files) != 1:
        raise FileNotFoundError('Image not found')
    await ctx.send(f'**{track}**', file=discord.File(track.path + files[0]))


@bot.command(name='cpinfo')
@tracklist.handle_input(regs=True, filetypes=('szs', 'kmp'))
async def cpinfo(ctx, track: TrackData):
    """ \\cpinfo <track name> - Get stats for track\'s checkpoint map """
    cpdata = track.cpdata
    if cpdata is None:    # not on spreadsheet
        if track.kmp_path() is None:
            await w.wkmpt_encode(track.szs_path(), track.path + 'course.kmp')
        with open(track.kmp_path(), 'rb') as f:
            rawkmp = kmp.parse(f)
        cpdata = utils.kmp.calculate_cpinfo(rawkmp, track.name, silent=True)

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


# TODO: reimplement \pop if needed?
'''@bot.command(name='pop')
async def pop(ctx, *args):
    pass
    popcat = Map(['name', 'id', 'desc'], [
        ['M1', 0, 'Current month (M1)'],
        ['M3', 1, 'Within last 3 months (M3)'],
        ['M6', 2, 'Within last 6 months (M6)'],
        ['M9', 3, 'Within last 9 months (M9)'],
        ['M12', 4, 'Within last 12 months (M12)']
    ])
    if not args:
        await ctx.send('\\pop [timeframe] <track name OR rank #> - Get track\'s popularity ranking\n'
                       '  Valid timeframes: M1, M3, M6, M9, M12')
        return

    # Check if timeframe is given
    if args[0].upper() in d.popcat.list('name') and len(args) > 1:
        c = d.popcat.get(args[0].upper())['id']
        args = list(args[1:])
    elif args[0].upper()[0] == 'M' and len([c for c in args[0] if c.isnumeric()]) == len(args[0]) - 1:
        await ctx.send(content='Valid timeframes: M1, M3, M6, M9, M12')
        return
    else:
        c = 1

    target_track = ''
    target_rank = 0

    # input is number
    if len(args) == 1 and args[0].isnumeric():
        s = await ctx.send('Searching...')
        target_rank = int(args[0])
        if not 0 < target_rank <= 218:
            await s.edit(content='Rank must be between 1 and 218')
            return

    # input is track name
    else:
        settings = {'ctgp': True, 'new': False, 'regs': False, 'atts': [],
                    'help': 'Track name not recognized.' + LIST_MSG}
        track = TrackData()
        await track.initialize(ctx, tl, args, settings)
        if not track.success:
            return
        s = track.s
        target_track = track.name

    rank = 0
    finalrow = None
    found = False

    # Iterate through rows on popularity page
    for i in range(3):
        url = f'https://wiimmfi.de/stats/track/mv/ctgp?m=json&p=std,c{c},0,{i*100}'
        html = BeautifulSoup(requests.get(url).text, 'html.parser')

        for row in html.table.tbody.find_all('tr'):
            identifier = ''
            idlist = []

            if len(row.find_all('a')) != 0:     # Use Wiimm ID
                identifier = row.find_all('a')[0]['href']
                idlist = [f'https://ct.wiimm.de/i/{sheet[1][i][4]}' for i in range(2, 220)]

            elif len(row.find_all('td', class_='LL')) != 0:     # Use SHA1
                identifier = row.find_all('td', class_='LL')[0].string.split()[1].upper()
                idlist = [sheet[1][i][5] for i in range(2, 220)]

            if identifier in idlist:
                rank += 1
                curtrack = tl[idlist.index(identifier)]
                if curtrack == target_track or rank == target_rank:
                    if not target_track:
                        target_track = curtrack
                    finalrow = row
                    found = True
                    break
        if found:
            desc = f'Time period: {d.popcat.get(c)["desc"]}\n' \
                   f'Races: {finalrow.find_all("td")[c+3].string} \n' \
                   f'Popularity rank: {rank}'
            await ctx.send(embed=discord.Embed(title=target_track, description=desc, color=0xCA00FF))
            await s.delete()
            return

    await s.edit(content='Track ranking could not be found.')'''


@bot.command(name='gcps')
@tracklist.handle_input(regs=True, filetypes=('szs', 'kmp'), extra_args=('sp',))
async def gcps(ctx, track: TrackData, *args):
    """ \\gcps [option] <track name> - Generates Desmos graph of the full track. """
    splitpaths = ('sp' in args)

    if track.kmp_path() is None:
        await w.wkmpt_encode(track.szs_path(), track.path + 'course.kmp')

    if splitpaths or f'{track.name}.desmos.html' not in os.listdir(track.path):
        with open(track.kmp_path(), 'rb') as f:
            rawkmp = kmp.parse(f)

        gcplist = gcpfinder.find(rawkmp, bounds=(-500000, 500000))
        html = gcpfinder.graph(rawkmp, gcplist, splitpaths, bounds=(-500000, 500000))

        append = f'{html}\n<!--{", ".join([str(g) for g in gcplist])}-->'
        if splitpaths:
            track.path = paths.TEMP
        with open(f'{track.path}{track.name}.desmos.html', 'w') as out:
            out.write(append)
    else:
        with open(f'{track.path}{track.name}.desmos.html', 'r') as f:
            gcplist = [s for s in f.read().split('\n')[-1][4:-3].split(', ') if s.isnumeric()]

    if len(gcplist) > 0:
        gcpfound = 'Ghost checkpoints found at: ' + ', '.join([str(g) for g in gcplist])
    else:
        gcpfound = 'No ghost checkpoints found.'

    msg = f'**{track.name}**\n{gcpfound}\nDownload file and open in browser:'
    await ctx.send(content=msg, file=discord.File(f'{track.path}{track.name}.desmos.html'))


@bot.command(name='random')
async def random_track(ctx, arg=''):
    track = tracklist[int(218*random.random() + 2)]
    if arg.lower() == 'all' or track.not_yet_broken():
        await info(ctx, track)
    else:
        await random_track(ctx)


if __name__ == '__main__':
    # TODO: this is stupid, add as extension instead
    try:
        # noinspection PyUnresolvedReferences
        import extra
        extra.initialize(bot)
    except ImportError:
        pass

    print(f'Process started: {datetime.now().strftime("%m/%d/%Y %H:%M:%S")}')
    bot.run(TOKEN)
