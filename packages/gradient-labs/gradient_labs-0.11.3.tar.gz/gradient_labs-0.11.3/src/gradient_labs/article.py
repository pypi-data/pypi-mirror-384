from enum import Enum


class ArticleUsageStatus(str, Enum):
    """Usage status defines whether the AI agent can use a published article or not."""

    ON: str = "on"
    OFF: str = "off"


class Visibility(str, Enum):
    """Visibility describes who can view the given item (e.g. help article)"""

    # PUBLIC means that the item is available to the general
    # public. For example, it is published on a public website.
    PUBLIC: str = "public"

    # USERS means that the item is only available to the
    # company's customers. For example, it is only accessible via an
    # app after sign-up.
    USERS: str = "users"

    # INTERNAL means that the item is only available to
    # the company's employees. For example, it is a procedure or SOP
    # that customers do not have access to.
    INTERNAL: str = "internal"


class PublicationStatus(str, Enum):
    """PublicationStatus describes the status of a help article."""

    # DRAFT means that the article is being written or
    # edited and is not published.
    DRAFT: str = "draft"

    # PUBLISHED means that the article is published.
    PUBLISHED: str = "published"
