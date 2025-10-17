from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from marshmallow import fields


class ProcedureStatus(str, Enum):
    """Identifies the publication status of a procedure."""

    # DRAFT indicates the procedure has been saved as a draft, but
    # won't be used in real conversations until it is promoted to live.
    DRAFT: str = "draft"

    # LIVE indicates the procedure is live and will be used in real
    # conversations.
    LIVE: str = "live"


@dataclass_json
@dataclass(frozen=True)
class UserDetails:
    """UserDetails describes a procedure author."""

    email: str


@dataclass_json
@dataclass(frozen=True)
class Procedure:
    """UserDetails describes a procedure author."""

    # id uniquely identifies the procedure.
    id: str

    # name is the user-given name of the procedure.
    name: str

    # status is the overall status of the procedure.
    status: ProcedureStatus

    # author is the user who originally created the procedure.
    author: UserDetails

    # created is the time at which the procedure was originally created.
    created: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )

    # updated is the time at which the procedure's status, metadata, or current
    # revision was last changed. It does *not* reflect revisions created as part
    # of testing unsaved changes.
    updated: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )

    # has_daily_limit is true if this procedure can only be executed for a maximum
    # number of conversations in a given day (defined below).
    has_daily_limit: bool

    # max_daily_conversations is the maximum number of conversations that a procedure
    # can be used in on a given day, when it is rate limited.
    max_daily_conversations: int
