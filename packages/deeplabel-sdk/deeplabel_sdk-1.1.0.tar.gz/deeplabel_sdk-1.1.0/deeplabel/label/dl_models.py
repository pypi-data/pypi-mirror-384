from typing import Any, Dict, List, Optional

from logging import getLogger
import deeplabel.client
import deeplabel
from deeplabel.basemodel import DeeplabelBase, MixinConfig
from enum import Enum

from deeplabel.exceptions import InvalidIdError


logger = getLogger(__name__)


class DlModelStepStatus(Enum):
    TBD = "TBD"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    ABORTED = "ABORTED"
    FAILURE = "FAILURE"


class _Status(MixinConfig):
    status: DlModelStepStatus
    start_time: float
    end_time: float
    error: Optional[None]


class _StatusWithProgress(MixinConfig):
    status: DlModelStepStatus
    start_time: float
    end_time: float
    error: Optional[None]
    progress: float


class DlModelStatus(MixinConfig):
    submission: _Status
    data_preparation: _StatusWithProgress
    training: _StatusWithProgress
    upload: _Status


class SequenceInfo(MixinConfig):
    length: int
    sampling_rate: int


class DlModelCategory(Enum):
    CLASSIFICATION = "CLASSIFICATION"
    DETECTION = "DETECTION"
    ACTION_RECOGNITION = "ACTION-RECOGNITION"


class DlModelType(Enum):
    ACTION = "ACTION"
    OBJECT = "OBJECT"


class DlModel(DeeplabelBase):
    dl_model_id: str
    url: Optional[str]
    description: Optional[str]
    sequence: Optional[SequenceInfo]
    status: DlModelStatus
    name: str
    architecture: str
    category: DlModelCategory
    type: DlModelType

    @classmethod
    def from_search_params(
        cls, params: Dict[str, Any], client: "deeplabel.client.BaseClient"
    ) -> List["DlModel"]:
        resp = client.get("/dlmodels", params)
        dlmodels = resp.json()["data"]["dlModels"]
        dlmodels = [cls(**dlmodel, client=client) for dlmodel in dlmodels]
        return dlmodels  # type: ignore

    @classmethod
    def from_dl_model_id(
        cls, dl_model_id: str, client: "deeplabel.client.BaseClient"
    ) -> "DlModel":
        dlmodels = cls.from_search_params({"dlModelId": dl_model_id}, client)
        if not dlmodels:
            raise InvalidIdError(f"No DlModel found with dlModelId: {dl_model_id}")
        return dlmodels[0]

    @property
    def generate_zip_url(self):
        resp = self.client.get(
            "/dlmodels/download", params={"dlModelId": self.dl_model_id}
        )
        if resp.status_code > 200:
            logger.info(
                f"Failed fetching dlmodel presigned url for {self.dl_model_id}. "
                f"Please make sure the zip exists in s3"
            )
            return None
        return resp.json()["data"]

    @property
    def names(self) -> List[str]:
        """Get dlmodel labels from model.names file.
        eg. ['labelA', 'labelB', 'labelC]
        where model output classes 0 to N corresponds to 0th to Nth index in the list
        """
        if "names" in self.extra:
            return self.extra["names"]
        resp = self.client.get(
            "/dlmodels/download",
            params={"dlModelId": self.dl_model_id, "modelNames": "true"},
        )
        self.extra["names"] = resp.json()["data"].splitlines()
        return self.extra["names"]

    @property
    def names_filter(self) -> List[str]:
        """Get dlmodel labels from model.names.filter or model.names.include file.
        eg. ['labelA', 'labelC']
        raises InvalidApiResponse if the neigher of the file exist.
        So use with caution 
        """
        if "names_filter" in self.extra:
            return self.extra["names_filter"]
        resp = self.client.get(
            "/dlmodels/download",
            params={"dlModelId": self.dl_model_id, "modelNamesFilter": "true"},
        )
        self.extra["names_filter"] = resp.json()["data"].splitlines()
        return self.extra["names_filter"]

