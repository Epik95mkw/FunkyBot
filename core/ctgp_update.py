import itertools
import zipfile
from io import BytesIO
import discord
from discord import app_commands
from discord.ext import commands
from discord.app_commands import command as slash_command

from api.spreadsheet import Spreadsheet
import api.chadsoft as chadsoft


SHEET_RANGE = ('A2:G219', 'A2:P219', None)


@app_commands.guild_only()
@app_commands.default_permissions()
class UpdateCommands(commands.GroupCog, group_name='ctgp-update'):

    def __init__(self, bot: commands.Bot, sheet: Spreadsheet):
        self.bot = bot
        self.sheet = sheet
        self.tracks_to_add = []
        self.tracks_to_remove = []
        self._stage = 0

    @property
    def stage(self):
        return self._stage

    @stage.setter
    def stage(self, n):
        self._stage = n
        print(f'Stage set to {n}.')



    @slash_command(name='check')
    async def check_new_tracks(self, interaction):
        """ #1. Check Chadsoft for new tracks """
        await interaction.response.defer()

        print('CTGP Update initiated')
        sha1_col = self.sheet[1].row_values(1).index('SHA1') + 1
        sheet_sha1s = self.sheet[1].col_values(sha1_col)[1:]
        chadsoft_sha1s = []
        removed_tracks = []
        added_tracks = []

        print('Fetching information from Chadsoft...')
        lbs = chadsoft.all_leaderboards()
        last = ''

        # If SHA1 exists on chadsoft but not sheet, it's a new track
        for t in lbs['leaderboards']:
            sha1 = t['trackId']
            if last == sha1:
                continue
            chadsoft_sha1s.append(sha1)
            if sha1 not in sheet_sha1s:
                added_tracks.append(t)
            last = sha1

        # If SHA1 exists on sheet but not chadsoft, it's a removed track
        for sha1 in sheet_sha1s:
            if sha1 not in chadsoft_sha1s:
                track_row = self.sheet[1].col_values(sha1_col).index(sha1) + 1
                removed_tracks.append(self.sheet[1].row_values(track_row)[0])

        # Set state
        self.tracks_to_add = added_tracks
        self.tracks_to_remove = removed_tracks
        self.stage = 1
        print('Response sent.')

        # Format response
        lines = ['%-30s%-30s' % (
            f'Added tracks ({len(added_tracks)}):',
            f'Removed tracks ({len(removed_tracks)}):'
        ), '']
        for added, removed in itertools.zip_longest(added_tracks, removed_tracks, fillvalue=''):
            lines.append('%-30s%-30s' % (added['name'], removed))
        out = '\n'.join(lines)
        await interaction.followup.send(
            f'```{out}```\n'
            f'If this is correct, use `/ctgp-update continue` to continue.\n'
            f'If this is not correct, use `/ctgp-update cancel` to cancel.'
        )


    @slash_command(name='prepare')
    async def zipfile_setup(self, interaction):
        """ #2. Create template zipfile with new track folders """
        await interaction.response.defer()

        with BytesIO() as buffer:
            with zipfile.ZipFile(buffer, 'w') as zf:
                zf.writestr('test', 'test')

            await interaction.followup.send('Zipfile', file=discord.File(buffer, filename='name.zip'))


    @slash_command(name='execute')
    async def execute_update(self, interaction):
        """ #3. Use zipfile to update spreadsheet and local track storage """
        await interaction.response.defer()

        async def respond(msg):
            await interaction.followup.send(msg, ephemeral=True)

        await respond('Not implemented')


    @slash_command(name='cancel')
    async def cancel_update(self, interaction):
        """ Cancel update and reset all update commands """
        self.stage = 0
        await interaction.response.send_message('Update canceled.', ephemeral=True)
