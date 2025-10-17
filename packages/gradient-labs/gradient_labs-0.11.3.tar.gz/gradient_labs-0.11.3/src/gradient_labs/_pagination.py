from typing import Optional
from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass(frozen=True)
class PaginationInfo:
    # next is a cursor to retrieve the next page of results.
    next: Optional[str] = None

    # prev is a cursor to retrieve the previous page of results.
    prev: Optional[str] = None
