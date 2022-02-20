from datetime import datetime

from telegram import ParseMode
from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update

from musicbot.config import config
from musicbot.model.handler import Handler
from musicbot.provider import Provider
from musicbot.util.exceptions import SpotifyEntityNotFoundException, YoutubeMetadataNotFoundException


forget_about_it_msgs = ["forget about it", "forget", "olvidalo", "olvídalo", "delete", "borrar", "fuera"]


class HandleAmend(Handler):
    def __init__(self, update: Update, context: CallbackContext) -> None:
        super().__init__(update, context)
        self.amend_message_id = update.message.reply_to_message.message_id
        self.amend_same_user = config.get("AMEND_SAME_USER", False)
        self.failed_submission = self.db.get_failed_submission(self.amend_message_id)
        self.handle()

    def check_amend(self) -> bool:
        if not self.failed_submission:
            self.logger.warn(f"amend failure [{self.amend_request_message_id}]: id not in db")
            self.delete_messages([self.amend_request_message_id, self.message_id])
            return False
        if self.amend_same_user and self.failed_submission.dj != self.dj:
            self.delete_messages([self.message_id])
            return False
        if self.command[0].strip().lower() in forget_about_it_msgs:
            ids = [self.amend_message_id, self.message_id, *self.failed_submission.failed_amends_message_ids]
            self.delete_messages(ids)
            self.db.remove_failed_submission(self.amend_message_id)
            return False
        return True

    def handle(self) -> None:
        if not self.check_amend():
            return

        try:
            # content passed as both uri and title arguments, provider will figure it out
            # users some times mistakenly add a !
            amend_content = self.command[0][1:] if self.command[0][0] == "!" else self.command[0]
            provider = Provider(amend_content, amend_content)
        except (SpotifyEntityNotFoundException, YoutubeMetadataNotFoundException):
            self.not_found()
            return

        if provider.uri:
            self.logger.info(f"valid uri [{provider.uri}]: fetching...")

            try:
                new_submission = provider.fetch(self.failed_submission.dj, datetime.now())
            except (SpotifyEntityNotFoundException):
                self.not_found()
                return

            # youtube url is original uri of a failed submission
            new_submission.track_url_youtube = self.failed_submission.original_uri

            submission_thread_message_ids = [
                *self.failed_submission.failed_amends_message_ids,
                self.message_id,
                self.amend_message_id,
                self.failed_submission.message_id,
            ]
            self.delete_messages(submission_thread_message_ids)

            self.context.bot.send_message(
                self.chat_id,
                text=new_submission.to_md(),
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            self.db.remove_failed_submission(self.amend_message_id)
            self.db.insert_submission(new_submission)

    def not_found(self) -> None:
        self.failed_submission.add_failed_amend(self.message_id, self.update.message.text)
        self.context.bot.edit_message_text(
            text=self.failed_submission.to_md(),
            chat_id=self.chat_id,
            message_id=self.failed_submission.amend_message_id,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True,
        )
        self.db.update_failed_submission(self.amend_message_id, self.failed_submission)
