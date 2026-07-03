
import logging
from typing import Optional

from DiploGM import perms
from DiploGM.manager import Manager
from discord.ext import commands

from DiploGM.models.player import Player
from DiploGM.models.poll import GameEndPoll
from DiploGM.utils.sanitise import find_discord_role, remove_prefix
from DiploGM.utils.send_message import send_message_and_file
from DiploGM.utils.timestamp_management import Timestamp


class PollDataFlags(commands.FlagConverter):
    description: Optional[str]
    deadline: Optional[Timestamp]
    public: Optional[bool]


manager = Manager()
logger = logging.getLogger(__name__)

class PollCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def _try_get_active_poll(self, ctx: commands.Context) -> Optional[GameEndPoll]:
        assert ctx.guild is not None
        board = manager.get_board(ctx.guild.id)
        poll = board.get_active_poll()
        if poll is None:
            await send_message_and_file(
                channel=ctx.channel,
                message=f"There is no active poll."
            )
        return poll

    @commands.group(name="poll", invoke_without_command=True)
    @perms.gm_only("Interact with a poll")
    async def poll(self, ctx: commands.Context):
        
        await send_message_and_file(
            channel=ctx.channel,
            message="You may use arguments: 'create', 'delete', 'edit', 'activate', 'deactivate'"
        )

    def _edit_poll(self, poll: GameEndPoll, flags: PollDataFlags):
        if flags.description is not None:
            poll.set_description(flags.description)
        if flags.deadline is not None:
            poll.set_deadline(flags.deadline) # type: ignore[arg-type]
        if flags.public is not None:
            poll.set_public(flags.public)

    @poll.command("create")
    @perms.gm_only("create a new poll")
    async def create_poll(self, ctx: commands.Context, *, flags: PollDataFlags):
        assert ctx.guild is not None
        board = manager.get_board(ctx.guild.id)
        poll = GameEndPoll()
        self._edit_poll(poll, flags)
        board.add_new_poll(poll)
        board.set_active_poll(poll)
        await send_message_and_file(
            channel=ctx.channel,
            message=f"Created poll with id {poll.id}"
        )

    @poll.command("delete")
    @perms.gm_only("delete an existing poll")
    async def delete_poll(self, ctx: commands.Context, poll_id: str):
        assert ctx.guild is not None
        board = manager.get_board(ctx.guild.id)
        board.delete_poll(poll_id)

    @poll.command("activate")
    @perms.gm_only("activate an existing poll")
    async def activate(self, ctx: commands.Context, poll_id: str):
        assert ctx.guild is not None
        board = manager.get_board(ctx.guild.id)
        board.set_active_poll(poll_id)

    @poll.command("deactivate")
    @perms.gm_only("deactivate the active poll")
    async def deactivate_poll(self, ctx: commands.Context):
        assert ctx.guild is not None
        board = manager.get_board(ctx.guild.id)
        board.set_active_poll(None)

    @poll.command("edit")
    @perms.gm_only("edit an existing poll")
    async def edit(self, ctx: commands.Context, poll_id: str, flags: PollDataFlags):
        assert ctx.guild is not None
        board = manager.get_board(ctx.guild.id)
        poll = board.get_poll(poll_id)
        self._edit_poll(poll, flags)

    @poll.command("vote")
    @perms.player("vote on the active poll")
    async def vote(self, ctx: commands.Context, vote: str, player: Optional[Player]):
        poll = self._try_get_active_poll(ctx)
        if poll is None:
            return
        if player is None:
            raise ValueError("Only players can vote")
        poll = board.get_active_poll()
        vote_value = poll.parse_vote(vote)
        poll.vote(player, vote_value)

    @poll.command("remove_vote")
    @perms.player("remove your vote on the active poll")
    async def remove_vote(self, ctx: commands.Context, player: Optional[Player]):
        if player is None:
            raise ValueError("Only players can remove their vote")
        poll.remove_vote(player)

    @poll.command("view")
    @perms.player("view information about a poll")
    async def view_poll(self, ctx: commands.Context, player: Optional[Player]):
        assert ctx.guild is not None
        board = manager.get_board(ctx.guild.id)
        
        args = ctx.message.content.strip().split()[2:] # gross way to get poll_id, given we can't add it as a parameter because of how @perms.player works
        logger.info(f"Args to view_poll: {args}")
        poll_id = args[0] if args else None
        if poll_id is None:
            poll = board.get_active_poll()
        else:
            poll = board.get_poll(poll_id)

        message = f"""Description:{poll.description or 'No description'}
Deadline: {poll.deadline or 'No deadline'}
Public: {poll.public}"""

        if poll.public: player_restriction = None
        else: player_restriction = player

        votes = poll.get_vote_to_players(player_restriction, board.get_players())
        for vote, player_set in votes.items():
            player_mentions = []
            for player in sorted(player_set, key=lambda k: k.name):
                role = find_discord_role(player, ctx.guild.roles)
                if role is not None: player_mentions.append(role.mention)
                else: player_mentions.append("@" + player.name)
            message += f"{vote.value}: {' '.join(player_mentions)}\n"

        await send_message_and_file(
            title=f"Poll {poll_id}",
            channel=ctx.channel,
            message=message,
        )

async def setup(bot):
    cog = PollCog(bot)
    await bot.add_cog(cog)
