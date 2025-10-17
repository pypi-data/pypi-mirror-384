from typing import Optional, List, Dict
from enum import Enum
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json


class ParameterType(str, Enum):
    """ParameterType determines the data type of a parameter."""

    # STRING indicates the parameter accepts string/text values.
    STRING: str = "string"


class BodyEncoding(str, Enum):
    """BodyEncoding determines how the HTTP body will be encoded."""

    # FORM indicates the body will be encoded using URL encoding.
    FORM: str = "application/x-www-form-urlencoded"

    # JSON indicates the body will be encoded as JSON.
    JSON: str = "application/json"


@dataclass_json
@dataclass
class ParameterOption:
    value: str
    text: str


@dataclass_json
@dataclass(frozen=True)
class ToolParameter:
    name: str
    description: str
    type: ParameterType
    required: Optional[bool] = False
    options: Optional[List[ParameterOption]] = field(default_factory=lambda: [])


@dataclass_json
@dataclass(frozen=True)
class ToolWebhookConfiguration:
    name: str


@dataclass_json
@dataclass(frozen=True)
class HTTPBodyDefinition:
    encoding: BodyEncoding
    json_template: Optional[str] = ""
    form_field_templates: Optional[Dict[str, str]] = None


@dataclass_json
@dataclass(frozen=True)
class HTTPDefinition:
    method: str
    url_template: str
    header_templates: Optional[Dict[str, str]] = None
    body: Optional[HTTPBodyDefinition] = None


@dataclass_json
@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    id: Optional[str] = None
    parameters: List[ToolParameter] = field(default_factory=lambda: [])
    webhook: Optional[ToolWebhookConfiguration] = None
    http: Optional[HTTPDefinition] = None


@dataclass_json
@dataclass(frozen=True)
class ToolUpdateParams:
    id: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=lambda: [])
    webhook: Optional[ToolWebhookConfiguration] = None
    http: Optional[HTTPDefinition] = None
    mock: Optional[bool] = False
