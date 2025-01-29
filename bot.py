import os
import random
from datetime import datetime
from glob import glob

import discord
from discord.ext import commands
from dotenv import load_dotenv

from api import chadsoft
from api.spreadsheet import Spreadsheet
from utils import szsreader, kmpreader, gcpfinder
from core import paths, cpinfo, command_utils
from core.tracklists import FilesystemTrackList, SpreadsheetTrackList

EMBED_COLOR = 0xCA00FF

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
SHEET_ID = os.getenv('SHEET_ID')
GUILD_ID = os.getenv('GUILD_ID')

fs_tracks = FilesystemTrackList(paths.CTGP)

spreadsheet = Spreadsheet(SHEET_ID, './token.json')
sheet_tracks = SpreadsheetTrackList(spreadsheet)

bot = commands.Bot(
    command_prefix='\\',
    help_command=None,
    intents=discord.Intents.all()
)


@bot.event
async def on_ready():
    if GUILD_ID is not None:
        # Only respond to commands in specified server
        for cmd in bot.commands:
            cmd.add_check(lambda ctx: str(ctx.guild.id) == GUILD_ID)
    if os.path.isdir('./extensions'):
        for file in os.listdir('./extensions'):
            if file.endswith('.py'):
                await bot.load_extension(f'extensions.{file[:-3]}')
    # await bot.add_cog(UpdateCommands(bot, spreadsheet), guilds=bot.guilds)
    await bot.change_presence(activity=discord.Game('\\help for commands'))
    print(f'Connected: {datetime.now().strftime("%m/%d/%Y %H:%M:%S")}')


@bot.event
async def on_command_error(ctx: commands.Context, error):
    if not isinstance(error, (commands.CommandNotFound, commands.CheckFailure)):
        await ctx.send(error)
        raise error.original if hasattr(error, 'original') else error


# COMMANDS #############################################################################################################


@bot.command(name='help')
async def cmd_help(ctx):
    cmdlist = '\n'.join(v.help for v in globals().values() if isinstance(v, commands.Command) and v.help)
    footer = '<trackname> accepts any custom track in CTGP. Track names are case insensitive and ' \
             'can be replaced with abbreviations ("dcr", "snes mc2", etc.).'
    embed = discord.Embed(title="Commands:", description=cmdlist[:3000] + '\n\n' + footer, color=EMBED_COLOR)
    await ctx.send(embed=embed)


@bot.command(name='links')
async def cmd_links(ctx):
    """ \\links - Get important CT resources """
    desc = (
        'CTGP Ultras Spreadsheet:\n'
        f'{spreadsheet.public_url}\n\n'
        'CTGP Tockdom Page:\n'
        'http://wiki.tockdom.com/wiki/CTGPR\n\n'
        'CTGP Track Files Dropbox:\n'
        'https://www.dropbox.com/sh/9phl0p4d663fmel/AAD0Xo4JyuYZng3AW4ynb2Nwa?dl=0\n\n'
        'CTGP Upcoming Track Updates:\n'
        'https://docs.google.com/spreadsheets/d/1xwhKoyypCWq5tCRTI69ijJoDiaoAVsvYAxz-q4UBNqM/edit?usp=sharing\n\n'
        'Lorenzi\'s KMP Editor:\n'
        'https://github.com/hlorenzi/kmp-editor/releases\n\n'
        'Brawlcrate:\n'
        'https://github.com/soopercool101/BrawlCrate/releases\n\n'
        'Download CTools:\n'
        'http://www.chadsoft.co.uk/ctools/setup/ctoolssetup.msi'
    )
    embed = discord.Embed(title='**Resources:**', description=desc, color=EMBED_COLOR)
    await ctx.send(embed=embed)


@bot.command(name='spreadsheet', aliases=['sheet', 'sheetlink'])
async def cmd_spreadsheet(ctx):
    """ \\spreadsheet - Get link to CTGP ultras spreadsheet """
    await ctx.send(spreadsheet.public_url)


@bot.command(name='info')
@command_utils.help_msg
async def cmd_info(ctx: commands.Context, *args):
    """ \\info <trackname> - Get general track information """
    if not args:
        raise command_utils.EmptyInputError()
    fsdata = fs_tracks.search(' '.join(args))
    if fsdata is None:
        return await ctx.send('Track name not recognized.')

    sheetdata = sheet_tracks.search(fsdata.name)
    if sheetdata is None:
        desc = (
            '*WARNING: missing spreadsheet data*'
            f'Author(s): {fsdata.authors}\n'
            f'Track Slot: {fsdata.slot}\n'
            f'Music Slot: {fsdata.music}\n'
            f'[CT Archive Page](https://ct.wiimm.de/i/{fsdata.sha1})'
        )
    else:
        desc = (
            f'Author(s): {fsdata.authors}\n'
            f'CTGP Version: {sheetdata.version}\n'
            f'Track Slot: {fsdata.slot}\n'
            f'Music Slot: {fsdata.music}\n'
            '\n'
            'Glitch Status:\n'
            f'> Unbreakable: {sheetdata.unbreakable}\n'
            f'> RTA status: {sheetdata.rta_status}\n'
            f'> TAS status: {sheetdata.tas_status or sheetdata.rta_status}\n'
            '\n'
            + (f'[Wiki Page]({sheetdata.wiki_url}) | ' if sheetdata.wiki_url else '') +
            f'[CT Archive Page](https://ct.wiimm.de/i/{fsdata.sha1})'
        )
    await ctx.send(embed=discord.Embed(title=fsdata.name, description=desc, color=EMBED_COLOR))


@bot.command(name='video')
@command_utils.help_msg
async def cmd_video(ctx: commands.Context, *args):
    """ \\video <trackname> - Get video of track\'s ultra shortcut """
    if not args:
        raise command_utils.EmptyInputError()
    sheetdata = sheet_tracks.search(' '.join(args))
    if sheetdata is None:
        return await ctx.send('Track name not recognized.')

    await ctx.send(content=f'**{sheetdata.name}**')
    if sheetdata.rta_video is not None:
        await ctx.send(f'RTA: {sheetdata.rta_status}\n{sheetdata.rta_video}')
    if sheetdata.tas_video is not None:
        await ctx.send(f'TAS: {sheetdata.tas_status}\n{sheetdata.tas_video}')
    if sheetdata.rta_video is None and sheetdata.tas_video is None:
        await ctx.send('No video available for this track.')


@bot.command(name='bkt')
@command_utils.help_msg
async def cmd_bkt(ctx: commands.Context, *args):
    """ \\bkt <trackname> [glitch/no-sc] [flap] [200cc] """
    if not args:
        raise command_utils.EmptyInputError()
    args = [a.lower() for a in args]
    track_args = []
    category = chadsoft.Category.NORMAL
    is_flap = False
    is_200 = False

    # Parse command
    for a in args:
        if a == 'glitch':
            category = chadsoft.Category.GLITCH
        elif a == 'no-sc':
            category = chadsoft.Category.NO_SC
        elif a == 'flap':
            is_flap = True
        elif a == '200cc' or a == '200':
            is_200 = True
        else:
            track_args.append(a)

    fsdata = fs_tracks.search(' '.join(args))
    if fsdata is None:
        return await ctx.send('Track name not recognized.')

    bkt_url = chadsoft.get_bkt_url(fsdata.slot, fsdata.sha1, category, is_flap, is_200)
    await ctx.send(bkt_url)


@bot.command(name='szs')
@command_utils.help_msg
async def cmd_szs(ctx: commands.Context, *args):
    """ \\szs <trackname> - Download track\'s szs file """
    if not args:
        raise command_utils.EmptyInputError()
    fsdata = fs_tracks.search(' '.join(args))
    if fsdata is None:
        return await ctx.send('Track name not recognized.')

    file = discord.File(fsdata.dir / fsdata.filename)
    await ctx.send(f'**{fsdata.name}**', file=file)


@bot.command(name='kmp')
@command_utils.help_msg
async def cmd_kmp(ctx: commands.Context, *args):
    """ \\kmp <trackname> - Download track\'s kmp and kcl files """
    if ctx.message.attachments:  # File input
        filepath = await command_utils.save_to_temp(ctx.message.attachments[0])
        if not str(filepath).endswith('.szs'):
            return await ctx.send('Invalid file type (expected .szs)')
        else:
            szsreader.extract_file_to(filepath, paths.TEMP / 'course.kmp', 'course.kmp')
            szsreader.extract_file_to(filepath, paths.TEMP / 'course.kcl', 'course.kcl')
        trackname = 'Attached Track'
        trackdir = paths.TEMP
    elif args:  # Text input
        fsdata = fs_tracks.search(' '.join(args))
        if fsdata is None:
            return await ctx.send('Track name not recognized.')
        trackname = fsdata.name
        trackdir = fsdata.dir
    else:
        raise command_utils.EmptyInputError()

    files = [
        discord.File(trackdir / 'course.kmp'),
        discord.File(trackdir / 'course.kcl'),
    ]
    await ctx.send(f'**{trackname}**', files=files)


@bot.command(name='img')
@command_utils.help_msg
async def cmd_img(ctx: commands.Context, *args):
    """ \\img <trackname> - Get image of track\'s checkpoint map """
    if not args:
        raise command_utils.EmptyInputError()
    fsdata = fs_tracks.search(' '.join(args))
    if fsdata is None:
        return await ctx.send('Track name not recognized.')

    images = glob(str(fsdata.dir / '*.png'))
    if not images:
        await ctx.send(f'No image found for {fsdata.name}.')
    else:
        await ctx.send(f'**{fsdata.name}**', file=discord.File(images[0]))


@bot.command(name='cpinfo')
@command_utils.help_msg
async def cmd_cpinfo(ctx: commands.Context, *args):
    """ \\cpinfo <trackname> - Get stats for track\'s checkpoint map """
    if ctx.message.attachments:  # File input
        trackname = 'Attached Track'
        filepath = await command_utils.save_to_temp(ctx.message.attachments[0])
        if str(filepath).endswith('.kmp'):
            kmp_path = filepath
        elif str(filepath).endswith('.szs'):
            kmp_path = paths.TEMP / 'course.kmp'
            szsreader.extract_file_to(filepath, kmp_path, 'course.kmp')
        else:
            return await ctx.send('Invalid file type (expected .szs or .kmp)')
    elif args:  # Text input
        fsdata = fs_tracks.search(' '.join(args))
        if fsdata is None:
            return await ctx.send('Track name not recognized.')
        trackname = fsdata.name
        kmp_path = fsdata.dir / 'course.kmp'
    else:
        raise command_utils.EmptyInputError()

    with open(kmp_path, 'rb') as f:
        cpdata = cpinfo.calculate_cpinfo(kmpreader.parse(f), trackname, silent=True)

    if cpdata.from_cp0 == '-1':
        await ctx.send('Checkpoint info unavailable for this track (multiple finish lines).')
        return

    desc = (
        f'Checkpoints: {cpdata.cp_count}\n'
        f'Checkpoint Groups: {cpdata.group_count}\n'
        f'Key Checkpoints: {cpdata.kcp_count}\n'
        f'Last Key Checkpoint: {cpdata.last_kcp}\n'
        '\n'
        f'95% from Checkpoint 0: {cpdata.from_cp0}\n'
        f'95% from Checkpoint 1: {cpdata.from_cp1}\n'
        f'Last Key Checkpoint %: {(float(cpdata.last_kcp_p) * 100):.2f}%\n'
        f'Maximum % for Ultra: {(float(cpdata.max_ultra_p) * 100):.2f}%\n'
    )

    embed = discord.Embed(title=trackname, description=desc, color=EMBED_COLOR)
    await ctx.send(content='', embed=embed)


@bot.command(name='gcps')
@command_utils.help_msg
async def cmd_gcps(ctx: commands.Context, *args):
    """ \\gcps [option] <trackname> - Generates Desmos graph of the full track. """
    args = [a.lower() for a in args]
    track_args = []
    splitpaths = False
    noquads = False
    dev = False

    # Parse command
    for a in args:
        if a in ('split-paths', 'sp'):
            splitpaths = True
        elif a in ('no-fill', 'nf'):
            noquads = True
        elif a == 'dev':
            dev = True
        else:
            track_args.append(a)

    if ctx.message.attachments:  # File input
        trackname = 'Attached Track'
        filepath = await command_utils.save_to_temp(ctx.message.attachments[0])
        if str(filepath).endswith('.kmp'):
            kmp_path = filepath
        elif str(filepath).endswith('.szs'):
            kmp_path = paths.TEMP / 'course.kmp'
            szsreader.extract_file_to(filepath, kmp_path, 'course.kmp')
        else:
            return await ctx.send('Invalid file type (expected .szs or .kmp)')
    elif track_args:  # Text input
        fsdata = fs_tracks.search(' '.join(track_args))
        if fsdata is None:
            return await ctx.send('Track name not recognized.')
        trackname = fsdata.name
        kmp_path = fsdata.dir / 'course.kmp'
    else:
        raise command_utils.EmptyInputError()

    with open(kmp_path, 'rb') as f:
        rawkmp = kmpreader.parse(f)

    gcplist = gcpfinder.find(rawkmp, bounds=(-500000, 500000))
    html = gcpfinder.graph(rawkmp, gcplist, splitpaths, (not noquads), dev, bounds=(-500000, 500000))

    paths.clear_temp()
    gcp_path = paths.TEMP / f'{trackname}.desmos.html'
    with open(gcp_path, 'w') as out:
        out.write(html)

    if len(gcplist) > 0:
        gcpfound = 'Ghost checkpoints found at: ' + ', '.join([str(g) for g in gcplist])
    else:
        gcpfound = 'No ghost checkpoints found.'

    msg = f'**{trackname}**\n{gcpfound}\nDownload file and open in browser:'
    await ctx.send(content=msg, file=discord.File(gcp_path))


@bot.command(name='random')
async def random_track(ctx: commands.Context):
    """ \\random - Get random track """
    trackname = random.choice(fs_tracks.names())
    await cmd_info(ctx, trackname)


@bot.command(name='sync')
@commands.is_owner()
async def sync_app_commands(ctx):
    """ Only bot owner can use. Syncs application commands. """
    msg = await ctx.send('Syncing...')
    synced = await bot.tree.sync(guild=ctx.guild)
    await msg.edit(content=f'Synced {len(synced)} app commands.')


if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
