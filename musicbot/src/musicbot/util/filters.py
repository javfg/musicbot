from telegram.ext.filters import MessageFilter
from telegram.message import Message

from musicbot.config import config


class ReplyToBotFilter(MessageFilter):
    def filter(self, effective_message: Message) -> bool:
        if not effective_message.reply_to_message:
            return

        return effective_message.reply_to_message.from_user.username == config["BOT_USERNAME"]


class ChatIdFilter(MessageFilter):
    def filter(self, effective_message: Message) -> bool:
        valid_chat_ids = config.get("VALID_CHAT_IDS")

        if not valid_chat_ids:
            return True

        return effective_message.chat.id in valid_chat_ids
