import re
from discord.ext import commands

_TIMESTAMP_RE = re.compile(
    r"<t:(\d{1,14}):[tTdDfFrR]>"
)

class Timestamp(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> int:
        if not isinstance(argument, str):
            raise commands.BadArgument("Must pass a string to timestamp converter")
        m = _TIMESTAMP_RE.fullmatch(argument.strip())
        if m:
            return int(m.group(1))
        raise commands.BadArgument(f"Cannot parse timestamp: {argument!r}")