import json
from typing import Optional

from musicbot.model.submissionType import SubmissionType


class Submission:
    """TODO: fill this"""

    def __init__(
        self,
        type: Optional[SubmissionType] = SubmissionType.empty,
    ) -> None:
        self.type = type
        self.dj = None
        self.not_found = False

    def __str__() -> str:
        return "[empty submission]"

    def to_json(self) -> str:
        return json.dumps(self.__dict__, default=str)

    def to_md() -> str:
        return ""
