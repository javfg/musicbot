import logging

from datetime import datetime

from requests.exceptions import HTTPError
from spotipy import SpotifyException
from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update
from youtube_dl.utils import DownloadError

from musicbot.model.failed_submission import FailedSubmission
from musicbot.model.handler import Handler
from musicbot.provider import Provider
from musicbot.util.exceptions import SpotifyEntityNotFoundException, YoutubeMetadataNotFoundException


logger = logging.getLogger(__name__)


class HandleSubmission(Handler):
    def __init__(self, update: Update, context: CallbackContext) -> None:
        super().__init__(update, context)
        self.message_uri = self.command[0][1:]
        self.handle()

    def not_found(self) -> None:
        failed_submission = FailedSubmission(self.chat_id, self.message_id, self.dj, self.message_uri)
        amend_message = self.send_message(failed_submission.to_md(), disable_web_page_preview=True)
        failed_submission.amend_message_id = amend_message.message_id
        self.db.insert_failed_submission(failed_submission)

    def handle(self) -> None:
        try:
            provider = Provider(self.message_uri)
        except (SpotifyEntityNotFoundException, YoutubeMetadataNotFoundException):
            self.not_found()
            return
        except (SpotifyException, HTTPError, DownloadError) as error:
            msg = getattr(error, "http_status", error)
            logger.error(f"provider returned {msg}")
            return

        if provider.uri:
            logger.info(f"valid uri [{self.message_uri}]: fetching...")

            try:
                submission = provider.fetch(self.dj, datetime.now())
            except (SpotifyEntityNotFoundException):
                self.not_found()
            except (SpotifyException, HTTPError, DownloadError) as error:
                msg = getattr(error, "http_status", error)
                logger.error(f"provider returned {msg}")
                return

            self.delete_message(chat_id=self.chat_id, message_id=self.message_id)
            self.send_message(submission.to_md())
            self.db.insert_submission(submission)
