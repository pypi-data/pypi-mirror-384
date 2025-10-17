from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import validator
import random

from pydantic import Field
from deeplabel.basemodel import DeeplabelBase


class DetectionLabelType(Enum):
    OBJECT = "OBJECT"
    ACTION = "ACTION"


class DetectionLabelCategory(Enum):
    DETECTION = "DETECTION"
    CLASSIFICATION = "CLASSIFICATION"


class DetectionLabel(DeeplabelBase):
    """Detection Label"""

    color: str  # hashvalue eg. \#efbg17
    name: str
    type: DetectionLabelType
    category: DetectionLabelCategory
    id: Optional[str]
    label_id: Optional[str]
    is_deleted: bool = False
    client: Any = Field(None, exclude=True)

    @validator("label_id", always=True)
    def validate_label_id(cls, v: Optional[str], values) -> str:  # type: ignore
        if v is None:
            assert (
                "id" in values
            ), f"DetectionLabel should either have label_id or id key. {v} ; {values}"
            return values["id"]  # type: ignore
        return v

    @classmethod
    def from_search_params(
        cls, params: Dict[str, Any], client: "deeplabel.client.BaseClient"
    ) -> List["DetectionLabel"]:
        resp = client.get("/labels", params=params)
        labels = resp.json()["data"]["labels"]
        return [cls(**label, client=client) for label in labels]

    @classmethod
    def create(
        cls,
        name: str,
        type: DetectionLabelType,
        category: DetectionLabelCategory,
        description: str,
        client: "deeplabel.client.DeeplabelClient",
        color: Optional[str] = None,
    ):
        if color is None:
            color = "#%06x" % random.randint(0, 0xFFFFFF) 
        resp = client.post('/labels', {
            "name": name,
            "type": type.value,
            "category": category.value,
            "description": description,
            "color": color
        })
        return cls(**resp.json()['data'])
        


# Import here to avoid cyclic reference
import deeplabel.client
