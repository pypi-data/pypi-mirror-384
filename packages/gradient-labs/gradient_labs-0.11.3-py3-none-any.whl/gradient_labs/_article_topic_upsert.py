from typing import Optional
from collections import defaultdict
from datetime import datetime

from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from marshmallow import fields

from .article import Visibility, PublicationStatus
from ._http_client import HttpClient


@dataclass_json
@dataclass(frozen=True)
class ArticleTopicUpsertParams:
    # id is your identifier for this topic
    id: str

    # name is the topic's name. This cannot be empty.
    name: str

    # visibility describes who can see this topic, ranging from the
    # whole world (public) through to employees only (internal).
    visibility: Visibility

    # status describes whether this topic is published or not.
    status: PublicationStatus

    # created is when the topic was first created.
    created: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )

    # last_edited is when the topic was last changed.
    last_edited: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )

    # description is an topic's tagline. It may be empty.
    description: Optional[str] = None

    # parent_id is the identifier for this topic's parent topic (if any).
    parent_id: Optional[str] = None

    # data optionally gives additional meta-data about the topic.
    data: Optional[dict] = field(default_factory=lambda: defaultdict(dict))


def upsert_article_topic(
    *, client: HttpClient, params: ArticleTopicUpsertParams
) -> None:
    body = params.to_dict()
    if params.parent_id is None:
        body.pop("parent_id")
    if params.description is None:
        body.pop("description")
    
    body["created"] = HttpClient.localize(params.created)
    body["last_edited"] = HttpClient.localize(params.last_edited)
    _ = client.post(
        path="topics",
        body=body,
    )
