from typing import List

from telegram import Message, ParseMode


class MessageActionsMixin:
    def send_message(self, message: str, **kwargs) -> Message:
        return self.context.bot.send_message(
            chat_id=self.chat_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN_V2,
            **kwargs,
        )

    def send_messages(self, messages: List[str], **kwargs) -> List[Message]:
        sent_messages = []
        for message in messages:
            sent_messages.append(self.send_message(message, **kwargs))
        return sent_messages

    def delete_message(self, **kwargs) -> bool:
        return self.context.bot.delete_message(**kwargs)

    def delete_messages(self, message_ids: List[int]) -> List[bool]:
        deleted_messages = []
        for message_id in message_ids:
            deleted_messages.append(self.context.bot.delete_message(chat_id=self.chat_id, message_id=message_id))
        return deleted_messages
