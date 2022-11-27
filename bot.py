import fnmatch
import json
import os
import random
from datetime import datetime

import discord
import requests
from bs4 import BeautifulSoup
from discord.ext.commands import Bot
from dotenv import load_dotenv

from utils import *
from utils import dicts as d, wiimms as w

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
sheet = Spreadsheet(os.getenv('SHEETS_KEY'), 'token.json')
tl = TrackList(sheet[0].row_names, [], d.regs.list('name'))
LIST_MSG = '\nUse \\list to view valid track names.'


bot = Bot(command_prefix='\\', help_command=None)


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game('\\help for commands'))
    print(f'Connected: {datetime.now().strftime("%m/%d/%Y %H:%M:%S")}')


# TODO: write better error handler
@bot.event
async def on_command_error(ctx, error):
    if not isinstance(error, discord.ext.commands.errors.CommandNotFound):
        await ctx.send(f'Something went wrong :(')
        raise error


# COMMANDS #############################################################################################################


@bot.command(name='help')
async def cmd_help(ctx):
    embed = discord.Embed(title="Commands:", description=d.cmdlist + LIST_MSG, color=0xCA00FF)
    await ctx.send(embed=embed)


@bot.command(name='links')
async def links(ctx):
    desc = f'CTGP Ultras Spreadsheet:\n{sheet.url}\n\n{d.links}'
    embed = discord.Embed(title='**Resources:**', description=desc, color=0xCA00FF)
    await ctx.send(embed=embed)


@bot.command(name='spreadsheet')
async def get_sheetlink(ctx):
    await ctx.send(sheet.url)


@bot.command(name='list')
async def tlist(ctx, arg=''):
    if not arg:
        ls = tl.ctgp
        if tl.new:
            ls += ['', 'Upcoming:'] + tl.new
    elif arg.lower() == 'ctgp':
        ls = tl.ctgp
    elif tl.new and arg.lower() == 'new':
        ls = tl.new
    else:
        await ctx.send('Unknown Argument.')
        return

    with open('tracklist.txt', 'w') as out:
        out.write('\n'.join(ls))
    await ctx.send(file=discord.File('tracklist.txt'))


@bot.command(name='info')
async def info(ctx, *args):
    settings = {'ctgp': True, 'new': False, 'regs': False, 'atts': [],
                'help': '\\info <track name> - Get track version, glitch status, and wiki page link' + LIST_MSG}
    track = CmdInstance()
    await track.initialize(ctx, tl, args, settings)
    if not track.success:
        return

    row1 = sheet[0][track.name]
    wiki = row1[0].link
    if wiki is None:
        wiki = '[link not found]'

    status = ''
    if row1[2][0:3] == 'Yes':
        status += d.gcat[row1[2]]
    else:
        status += d.gcat[row1[3]]
        if len(row1) > 4 and row1[4] in d.gcat:
            if status == 'Not Glitched':
                status = d.gcat[row1[4]]
            else:
                status += ', ' + d.gcat[row1[4]]

    row2 = sheet[1][track.name]
    archive = f'<https://ct.wiimm.de/i/{row2[4]}>' if row2[4] != '--' else 'N/A'

    desc = f'Creator(s): {row2[2]}\n' \
           f'CTGP Version: {row1[1]}\n' \
           f'Track Slot: {row2[3]}\n' \
           f'CT Archive ID: {row2[4]}\n' \
           f'\n' \
           f'Glitch Status: {status}\n' \
           f'\n' \
           f'Wiki Page: <{wiki}>\n' \
           f'CT Archive Page: {archive}'

    await ctx.send(embed=discord.Embed(title=track.name, description=desc, color=0xCA00FF))
    await track.s.delete()


@bot.command(name='vid')
async def vid(ctx, *args):
    settings = {'ctgp': True, 'new': False, 'regs': False, 'atts': [],
                'help': '\\vid <track name> - Get video of track\'s ultra shortcut' + LIST_MSG}
    track = CmdInstance()
    await track.initialize(ctx, tl, args, settings)
    if not track.success:
        return

    await track.s.edit(content=f'**{track.name}**')

    rta = sheet[0][track.name][3]
    tas = sheet[0][track.name][4]

    if rta.link is not None:
        status = d.gcat[rta] if rta in d.gcat else rta
        await ctx.send(f'{status}: \n{rta.link}')

    if tas.link is not None:
        status = d.gcat[tas] if tas in d.gcat else tas
        await ctx.send(f'{status}: \n{tas.link}')

    if rta.link is None and tas.link is None:
        await ctx.send('There is no video available for this track.')


@bot.command(name='bkt')
async def get_bkt(ctx, *args):
    if not args:
        await ctx.send('\\bkt <track name> [glitch/no-sc] [flap] [200cc]')
        return

    args = [a.lower() for a in args]
    params = True
    category = 0
    is_flap = ''
    is_200 = False

    # Parse command
    while params:
        if len(args) > 0:
            a = args.pop()
            if a == 'glitch':
                category = 1
            elif a == 'no-sc':
                category = 2
            elif a == 'flap':
                is_flap = '-fast-lap'
            elif a == '200cc' or a == '200':
                is_200 = True
            else:
                args += [a]
                params = False

    settings = {'ctgp': True, 'new': False, 'regs': True, 'atts': [], 'help': 'Track name not recognized.' + LIST_MSG}
    track = CmdInstance()
    await track.initialize(ctx, tl, args, settings)
    if not track.success:
        return

    # Build URL & get JSON
    if is_200:
        category += 4
    suffix = f'0{category}{is_flap}'

    if track.name in tl.regs:
        d_ = d.regs.get(track.name)
        lb_url = f'https://tt.chadsoft.co.uk/leaderboard/{d_["slot"]}/{d_["sha1"]}/{suffix}'
    else:
        row = sheet[1][track.name]
        lb_url = f'https://tt.chadsoft.co.uk/leaderboard/{row[3][0:2]}/{row[5]}/{suffix}'

    lb_req = requests.get(lb_url + '.json')
    lb_req.encoding = 'utf-8-sig'
    try:
        lb = lb_req.json()
    except json.decoder.JSONDecodeError:
        await track.s.edit(content='Category does not exist.')
        return

    bkt_url = 'https://chadsoft.co.uk/time-trials' + lb['ghosts'][0]['_links']['item']['href'][0:-4] + 'html'
    await ctx.send(bkt_url)
    await track.s.delete()


@bot.command(name='szs')
async def szs(ctx, *args):
    settings = {'ctgp': True, 'new': True, 'regs': True, 'atts': [],
                'help': '\\szs <track name> - Download track\'s szs file' + LIST_MSG}
    track = CmdInstance()
    await track.initialize(ctx, tl, args, settings)
    if not track.success:
        return

    title = f'**{track}**'
    if track.name in d.cleaned:
        title += '\n(Note: Use \kmp to get clean KCL file)'

    files = fnmatch.filter(os.listdir(track.path), '*.szs')
    if len(files) != 1:
        await ctx.send(f'File could not be found. <@218679637742583808>')
    else:
        await ctx.send(title, file=discord.File(track.path + files[0]))
    await track.s.delete()


@bot.command(name='kmp')
async def get_kmp(ctx, *args):
    settings = {'ctgp': True, 'new': True, 'regs': True, 'atts': ['.szs'],
                'help': '\\kmp <track name> - Download track\'s kmp and kcl files' + LIST_MSG}
    track = CmdInstance()
    await track.initialize(ctx, tl, args, settings)
    if not track.success:
        return

    if track.category == 'att':
        if not await w.kmp_encode(track.path, track.file):
            await track.s.edit(content='KMP decode failed: File not found.')
            return
        if not await w.kcl_encode(track.path, track.file):
            await track.s.edit(content='KCL decode failed: File not found.')
            return

    title = f'**{track.name}**'
    if track.name in d.cleaned:
        title += '\n(Note: KCL modified to remove invalid triangles)'

    files = [discord.File(track.kmp(), filename='course.kmp'),
             discord.File(track.kcl(), filename='course.kcl')]
    await ctx.send(f'**{track}**', files=files)
    await track.s.delete()


@bot.command(name='kmptext')
async def kmptext(ctx, *args):
    settings = {'ctgp': True, 'new': True, 'regs': True, 'atts': ['.szs', '.kmp'],
                'help': '\\kmptext <track name> - Get track kmp in both raw and text form' + LIST_MSG}
    track = CmdInstance()
    await track.initialize(ctx, tl, args, settings)
    if not track.success:
        return

    files = []

    if track.att_type == '.szs':
        if not await w.kmp_encode(track.path, track.file):
            await track.s.edit(content='KMP encode failed: File not found.')
            return
        files += [discord.File(track.kmp(), filename='course.kmp')]

    await w.kmp_decode(track.path, track.file)
    files += [discord.File(track.txt())]

    await ctx.send(f'**{track.name}**', files=files)
    await track.s.delete()


@bot.command(name='kcltext')
async def kcltext(ctx, *args):
    settings = {'ctgp': True, 'new': True, 'regs': True, 'atts': ['.szs', '.kcl'],
                'help': '\\kcltext <track name> - Get track kcl in both raw and text form' + LIST_MSG}
    track = CmdInstance()
    await track.initialize(ctx, tl, args, settings)
    if not track.success:
        return

    files = []

    if track.att_type == '.szs':
        if not await w.kcl_encode(track.path, track.file):
            await track.s.edit(content='KCL encode failed: File not found.')
            return
        files += [discord.File(track.kcl(), filename='course.kcl')]

    await w.kcl_flags(track.path)
    files += [discord.File(track.path + 'kcl.txt')]

    title = f'**{track.name}**'
    if track.name in d.cleaned:
        title += '\n(Note: KCL modified to remove invalid triangles)'

    await ctx.send(title, files=files)
    await track.s.delete()


@bot.command(name='img')
async def cpmap1(ctx, *args):
    settings = {'ctgp': True, 'new': True, 'regs': True, 'atts': ['.szs', '.kmp'],
                'help': '\\img <track name> - Get image of track\'s checkpoint map' + LIST_MSG}
    track = CmdInstance()
    await track.initialize(ctx, tl, args, settings)
    if not track.success:
        return

    files = fnmatch.filter(os.listdir(track.path), '*.png')
    if len(files) != 1:
        await track.s.edit(content='Generating image...')
        if not await w.kmp_draw(track.path, track.file):
            await track.s.edit('File not found.')
            return
        files = fnmatch.filter(os.listdir(track.path), '*.png')
    await ctx.send(f'**{track}**', file=discord.File(track.path + files[0]))
    await track.s.delete()


@bot.command(name='id')
async def cpmap2(ctx, *args):
    settings = {'ctgp': True, 'new': False, 'regs': True, 'atts': [], 'help': '\\id <track name>'}
    track = CmdInstance()
    await track.initialize(ctx, tl, args, settings)
    if not track.success:
        return

    await track.s.edit(content=f'**{track.name}**')
    if track.name in tl.regs:
        abbrev = d.regs.get(track.name)['alias']
        await ctx.send(f'!cp {abbrev}')
    else:
        wid = sheet[1][track.name][4]
        await ctx.send(f'!id {wid}' if wid != '--' else 'Archive ID not found.')


@bot.command(name='cpinfo')
async def cpinfo(ctx, *args):
    settings = {'ctgp': True, 'new': True, 'regs': True, 'atts': ['.szs', '.kmp'],
                'help': '\\cpinfo <track name> - Get stats for track\'s checkpoint map'}
    track = CmdInstance()
    await track.initialize(ctx, tl, args, settings)
    if not track.success:
        return

    if track.category != 'ctgp':    # not on spreadsheet
        if not await w.kmp_encode(track.path, filename=track.file):
            await track.s.edit(content='KMP extraction failed.')
            return
        with open(track.kmp(), 'rb') as f:
            rawkmp = kmp.parse(f)
        values = w.calculate_cpinfo(rawkmp, track, silent=True)
        values = [str(a) for a in values] + ['Unknown']

    else:   # is on spreadsheet
        row = sheet[1].read_row(track.name)
        if not row[14]:
            row[14] = 'None'
        values = row[6:15]

    if values[4] == '-1':
        await track.s.edit(content='Checkpoint info unavailable for this track (multiple finish lines).')
        return

    desc = f'Checkpoints: {values[1]}\n' \
           f'Checkpoint Groups: {values[0]}\n' \
           f'Key Checkpoints: {values[2]}\n' \
           f'Last Key Checkpoint: {values[3]}\n' \
           '\n' \
           f'95% from Checkpoint 0: {values[4]}\n' \
           f'95% from Checkpoint 1: {values[5]}\n' \
           'Last Key Checkpoint %: ' + '{:.2f}'.format(float(values[6]) * 100) + '%\n' \
           'Maximum % for Ultra: ' + '{:.2f}'.format(float(values[7]) * 100) + '%\n' \
           '\n' \
           f'Anomalies: {values[8]}'

    embed = discord.Embed(title=track.name, description=desc, color=0xCA00FF)
    await ctx.send(content='', embed=embed)
    await track.s.delete()


@bot.command(name='pop')
async def pop(ctx, *args):
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
        track = CmdInstance()
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

    await s.edit(content='Track ranking could not be found.')


@bot.command(name='gcps')
async def gcps(ctx, *args):
    settings = {'ctgp': True, 'new': True, 'regs': True, 'atts': ['.szs', '.kmp'],
                'help': '\\gcps [option] <track name> - Generates Desmos graph of the full track.'}

    option = ''
    args = list(args)
    if args and args[0] in ['sp']:
        option = args.pop(0)

    track = CmdInstance()
    await track.initialize(ctx, tl, args, settings)
    if not track.success:
        return

    if not await w.kmp_encode(track.path, filename=track.file):
        await track.s.edit(content='KMP extraction failed.')
        return

    if option or f'{track.name}.desmos.html' not in os.listdir(track.path):
        with open(track.kmp(), 'rb') as f:
            rawkmp = kmp.parse(f)

        gcplist = gcpfind(rawkmp, bounds=(-500000, 500000))
        html = gcpgraph(rawkmp, gcplist, option, bounds=(-500000, 500000))

        txt = f'{html}\n<!--{", ".join([str(g) for g in gcplist])}-->'
        if len(gcplist) > 0:
            gcpfound = 'Ghost checkpoints found at: ' + ', '.join([str(g) for g in gcplist])
        else:
            gcpfound = 'No ghost checkpoints found.'

        if option:
            track.path = paths.TEMP
        with open(f'{track.path}{track.name}.desmos.html', 'w') as out:
            out.write(txt)
    else:
        with open(f'{track.path}{track.name}.desmos.html', 'r') as f:
            gcpfound = 'Ghost checkpoints found at: ' + f.read().split('\n')[-1][4:-3]

    msg = f'**{track.name}**\n{gcpfound}\nDownload file and open in browser:'
    await ctx.send(content=msg, file=discord.File(f'{track.path}{track.name}.desmos.html'))
    await track.s.delete()


@bot.command(name='random')
async def rand(ctx, arg=''):
    row = sheet[0][int(218*random.random() + 2)]
    ng = ['Not Glitched', 'Lap 4 Bug', 'NLC Glitch']
    if arg.lower() == 'all':
        await info(ctx, row[0])
    else:
        if row[2][0:3] != 'Yes' and len(row) >= 4 and row[3] in ng \
                and not (len(row) > 4 and row[4] in d.gcat):
            await info(ctx, row[0])
        else:
            await rand(ctx)


if __name__ == '__main__':
    try:
        # noinspection PyUnresolvedReferences
        import extra
        extra.initialize(bot)
    except ImportError:
        pass

    print(f'Process started: {datetime.now().strftime("%m/%d/%Y %H:%M:%S")}')
    bot.run(TOKEN)
