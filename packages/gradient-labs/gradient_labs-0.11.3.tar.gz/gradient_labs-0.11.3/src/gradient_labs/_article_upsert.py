from typing import Optional, Any
from collections import defaultdict
from datetime import datetime

from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from marshmallow import fields

from .article import Visibility, PublicationStatus
from ._http_client import HttpClient


@dataclass_json
@dataclass(frozen=True)
class UpsertArticleParams:

    # id is your identifier of choice for this article.
    id: str

    # visibility describes who can access this article, ranging from the
    # whole world (public) through to employees only (internal).
    visibility: Visibility

    # status describes whether this article is published or not.
    status: PublicationStatus

    # created is when the article was first created.
    created: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )

    # last_edited is when the article was last changed.
    last_edited: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )

    # topic_id optionally identifies the topic that this
    # article is associated with. If given, you must have created
    # the topic first (see: UpsertArticleTopic)
    topic_id: Optional[str] = None

    # author_id optionally identifies the user who last edited the article
    author_id: Optional[str] = None

    # title is the article's title. It may be empty if the article is a draft.
    title: Optional[str] = None

    # description is an article's tagline. It may be empty.
    description: Optional[str] = None

    # body is the main contents of an article. It may be empty if the article is a draft.
    body: Optional[str] = None

    # data optionally gives additional meta-data about the article.
    data: Optional[Any] = field(default_factory=lambda: defaultdict(dict))


def upsert_article(*, client: HttpClient, params: UpsertArticleParams) -> None:
    body = params.to_dict()
    if params.title is None:
        body.pop("title")
    if params.description is None:
        body.pop("description")
    if params.topic_id is None:
        body.pop("topic_id")
    if params.author_id is None:
        body.pop("author_id")
    if params.body is None:
        body.pop("body")
    
    body["created"] = HttpClient.localize(params.created)
    body["last_edited"] = HttpClient.localize(params.last_edited)
    _ = client.post(
        path="articles",
        body=body,
    )
