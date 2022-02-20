import logging

from datetime import datetime
from typing import List

from tinydb import Query, TinyDB
from tinydb.queries import QueryLike
from tinydb.storages import JSONStorage
from tinydb_serialization import SerializationMiddleware
from tinydb_serialization.serializers import DateTimeSerializer

from musicbot.model.failed_submission import FailedSubmission
from musicbot.model.submission import Submission
from musicbot.util.serializers import SubmissionTypeSerializer


class DB:
    def __init__(self, submissions_db: TinyDB, failed_submissions_db: TinyDB) -> None:
        self.submissions_db = submissions_db
        self.failed_submissions_db = failed_submissions_db

    def insert_submission(self, submission: Submission) -> int:
        return self.submissions_db.insert({**vars(submission)})

    def get_submissions(self, cond: QueryLike) -> List[Submission]:
        """Get all submissions."""
        submissions = self.submissions_db.search(cond)
        return [Submission(**s) for s in submissions]

    def get_submissions_since(self, since: datetime) -> List[Submission]:
        q = Query()
        timeframe_end = datetime.now()
        submissions = self.get_submissions((q.submission_date > since) & (q.submission_date < timeframe_end))
        return sorted(submissions, key=lambda x: x.dj, reverse=True)

    def get_submissions_for_dj(self, dj: str) -> List[Submission]:
        q = Query()
        return self.get_submissions(q.dj.test(lambda x: x.lower() == dj.lower()))

    def get_submissions_by_tag(self, tag: str) -> List[Submission]:
        """Get submissions tagged with `tag`."""
        q = Query()
        return self.get_submissions(q.artist_genre_tags.any(tag))

    def insert_failed_submission(self, failed_submission: FailedSubmission) -> int:
        return self.failed_submissions_db.insert({**vars(failed_submission)})

    def get_failed_submission(self, amend_message_id: int) -> FailedSubmission:
        q = Query()
        fs = self.failed_submissions_db.get(q.amend_message_id == amend_message_id) or {}
        return FailedSubmission(**fs)

    def remove_failed_submission(self, amend_message_id: int) -> int:
        q = Query()
        return self.failed_submissions_db.remove(q.amend_message_id == amend_message_id)

    def update_failed_submission(self, amend_message_id: int, failed_submission: FailedSubmission) -> int:
        q = Query()
        return self.failed_submissions_db.update({**vars(failed_submission)}, (q.amend_message_id == amend_message_id))


class DBManager:
    def __init__(self, valid_chat_ids: List[int] = []) -> None:
        self.dbs = {}
        self.logger = logging.getLogger(__name__)
        self.init_dbs(valid_chat_ids)

    def init_dbs(self, chat_ids: List[int]) -> None:
        s = SerializationMiddleware(JSONStorage)
        s.register_serializer(DateTimeSerializer(), "datetimeserializer")
        s.register_serializer(SubmissionTypeSerializer(), "submissiontypeserializer")

        for chat_id in chat_ids:
            self.logger.info(f"init db for [chat_id: {chat_id}]")
            self.dbs[f"{chat_id}-submissions"] = TinyDB(f"db/{chat_id}-submissions.json", storage=s)
            self.dbs[f"{chat_id}-failed-submissions"] = TinyDB(f"db/{chat_id}-failed-submissions.json")

    def get_db(self, chat_id) -> DB:
        submissions_db = self.dbs[f"{chat_id}-submissions"]
        failed_submissions_db = self.dbs[f"{chat_id}-failed-submissions"]

        return DB(submissions_db, failed_submissions_db)
