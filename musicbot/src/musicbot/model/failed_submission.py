import json
from typing import Optional

from musicbot.util import _


class FailedSubmission:
    """The class representing a failed Submission.

    Contains the information needed in case somebody amends it later.

    :param chat_id: The telegram chat_id for the chat the submission was made to.
    :param message_id: The telegram message_id for the message containing the submission.
    :param dj: The name of the user who made the submission.
    :param original_uri: The uri sent by the dj in the submission (which failed being fetched).
    """

    def __init__(
        self,
        chat_id: str,
        message_id: str,
        dj: str,
        original_uri: str,
        amend_message_id: Optional[str] = None,
        failed_amends_message_ids: Optional[str] = None,
        failed_amends_message_contents: Optional[str] = None,
    ) -> None:
        self.chat_id = chat_id
        self.message_id = message_id
        self.dj = dj
        self.original_uri = original_uri
        self.amend_message_id = amend_message_id
        self.failed_amends_message_ids = failed_amends_message_ids or []
        self.failed_amends_message_contents = failed_amends_message_contents or []

    def __str__(self) -> str:
        return f"[failed] uri: [{self.original_uri}]"

    def to_json(self) -> str:
        return json.dumps(self.__dict__, default=str)

    def add_failed_amend(self, message_id: str, message_content: str) -> None:
        self.failed_amends_message_ids.append(message_id)
        self.failed_amends_message_contents.append(message_content)

    def to_md(self) -> str:
        retries = len(self.failed_amends_message_ids)
        attempts = ""
        if self.failed_amends_message_contents:
            entries = "\n".join([f"  • {_(content)}" for content in self.failed_amends_message_contents])
            attempts += f"\n{retries} attempt\\(s\\) made:\n{entries}"

        md_string = (
            f"*❌ Youtube video* {_(self.original_uri)} *submitted by* {_(self.dj)} *has no metadata\\!*\n"
            f"Reply to this message with the Spotify uri or link\n"
            f"\\(You can also tell me to *forget about it*\\)\\.\n"
            f"{attempts}"
        )

        return md_string
