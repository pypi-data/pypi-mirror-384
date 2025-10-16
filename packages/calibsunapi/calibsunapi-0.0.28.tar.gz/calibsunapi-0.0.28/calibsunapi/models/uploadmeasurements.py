from dataclasses import dataclass
from enum import Enum


class UploadMeasurementsFormats(Enum):
    JSON = "json"
    CSV = "csv"

    def __get__(self, instance, owner):
        return self.value


@dataclass
class UploadLinkMeasurementsResponse:
    url: str
    fields: dict[str, str]
