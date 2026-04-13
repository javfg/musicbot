from telegram import Update
from telegram.constants import ParseMode

from musicbot.context import MusicbotContext
from musicbot.security import secured
from musicbot.util import _


@secured
async def handle_help(update: Update, context: MusicbotContext) -> None:
    if update.message is None:
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            f"Hi\\! I'm {_(context.bot.name)}, *your personal DJ\\!*\n\n"
            'I can look for songs, albums or artists for you if you send me some text by mentioning me: \\write '
            f'@{_(context.bot.username)} and type something, I will suggest you stuff to pick up from\\.'
            '\n\n'
            "The list I'll show you will have items starting by:\n"
            '  • 👩‍🎤 for *artists*\n'
            '  • 💿 for *albums*\n'
            '  • 🎵 for *tracks*\n\n'
            "Just *pick one* of the suggestions and I'll do the rest\\.\n\n"
            "You can also put a *YouTube* or *Spotify* link in there and I'll figure things out\\. Most of the time\\."
            '\n\n'
            '*If I mess things up*, you can correct me by replying to my message with the correct spotify, youtube '
            "or wikipedia links and I'll fix them for you in your scrobble\\."
            '\n\n'
            "I can do some other stuff, you can see it by writing `/` in the message box and I'll show you a list"
            'of commands\\.'
        ),
        parse_mode=ParseMode.MARKDOWN_V2,
    )
