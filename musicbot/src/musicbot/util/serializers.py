from tinydb_serialization import Serializer

from musicbot.model.submission_type import SubmissionType


class SubmissionTypeSerializer(Serializer):
    OBJ_CLASS = SubmissionType

    def encode(self, obj):
        return obj.value

    def decode(self, s):
        return SubmissionType(s)
