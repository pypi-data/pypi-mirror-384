from dataclasses import dataclass
from dataclasses_json import dataclass_json

from .article import ArticleUsageStatus
from ._http_client import HttpClient


@dataclass_json
@dataclass(frozen=True)
class SetArticleUsageStatusParams:
    usage_status: ArticleUsageStatus


def set_article_usage_status(
    *, client: HttpClient, id: str, params: SetArticleUsageStatusParams
) -> None:
    _ = client.post(
        path=f"articles/{id}/usage-status",
        body={"usage_status": params.usage_status.value},
    )
