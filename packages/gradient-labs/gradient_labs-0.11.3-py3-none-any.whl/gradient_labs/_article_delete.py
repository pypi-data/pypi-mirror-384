from ._http_client import HttpClient


def delete_article(*, client: HttpClient, id: str) -> None:
    _ = client.delete(
        path=f"articles/{id}",
        body=None,
    )
