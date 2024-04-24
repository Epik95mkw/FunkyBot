from discord import app_commands
from discord.ext import commands
from discord.app_commands import command as slash_command

from api.spreadsheet import Spreadsheet
import api.chadsoft as chadsoft

'''
NEW CTGP UPDATE FLOW

/ctgp-update start
    get old sha1s from spreadsheet
    get new sha1s from chadsoft
    compare sha1s to extract new tracks and removed tracks
    if no new tracks:
        send message "No new tracks found. Update aborted."
    else:
        update UPDATE_STATE
        send message (
           "Track slots being updated: {number of changed tracks}
            Tracks being added: {list new tracks}
            Tracks being removed: {list removed tracks}

            If this is correct, use `/ctgp-update continue` to continue.
            If this is not correct, use `/ctgp-update cancel` to cancel."
        )

'''

CT_COUNT = 218
SHEET_RANGE = ('A2:G219', 'A2:P219', None)


@app_commands.guild_only()
@app_commands.default_permissions()
class AppCommands(commands.GroupCog, group_name='ctgp-update'):
    def __init__(self, bot: commands.Bot, sheet: Spreadsheet):
        self.bot = bot
        self.sheet = sheet
        self.stage = 0
        self.tracks_to_add = []
        self.tracks_to_remove = []

    @slash_command(name='start')
    async def check_new_tracks(self, interaction, new_track_count: int):
        """ Start bot update process """
        print('CTGP Update initiated')
        local_sha1s = self.sheet[1].read_col('SHA1')
        chadsoft_sha1s = []
        removed_tracks = []
        added_tracks = []

        async def respond(msg):
            await interaction.response.send_message(msg, ephemeral=True)

        print('Fetching information from Chadsoft...')
        lbs = chadsoft.all_leaderboards()
        last = ''

        # If SHA1 exists on chadsoft but not local, it's a new track
        for t in lbs['leaderboards']:
            sha1 = t['trackId']
            if last == sha1:
                continue
            chadsoft_sha1s.append(sha1)
            if sha1 not in local_sha1s:
                added_tracks.append(t)
            last = sha1

        # Check if total track count is wrong
        if len(local_sha1s) != CT_COUNT or len(chadsoft_sha1s) != CT_COUNT:
            await respond(
                f'Error: Unexpected number of total tracks\n{CT_COUNT=}\n{len(local_sha1s)=}\n{len(chadsoft_sha1s)=}')

        # If SHA1 exists on local but not chadsoft, it's a removed track
        for sha1 in local_sha1s:
            if sha1 not in chadsoft_sha1s:
                removed_tracks.append(self.sheet[1].get_row_name('SHA1', sha1))

        # Check if new track count is wrong
        if len(removed_tracks) != new_track_count or len(added_tracks) != new_track_count:
            await respond(
                f'Unexpected number of new tracks\n{new_track_count=}\n{len(removed_tracks)=}\n{len(added_tracks)=}')

        # Set state
        self.tracks_to_add = added_tracks
        self.tracks_to_remove = removed_tracks
        self.stage = 1

        # Format response
        lines = ['%-30s%-30s' % ('\nAdded tracks:', ' Removed tracks:')]
        for i in range(new_track_count):
            lines.append('%-30s%-30s' % (added_tracks[i]['name'], removed_tracks[i]))
        out = '\n'.join(lines)
        await respond(
            f'Track slots being updated: {new_track_count}\n'
            f'```{out}```\n'
            f'If this is correct, use `/ctgp-update continue` to continue.\n'
            f'If this is not correct, use `/ctgp-update cancel` to cancel.'
        )