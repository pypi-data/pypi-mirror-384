"""
Module to get detections data
"""
from enum import Enum
from typing import Any, List, Optional, Dict
from pydantic import Field
from deeplabel.basemodel import DeeplabelBase
import deeplabel.client
from deeplabel.exceptions import InvalidIdError
from deeplabel.infer.types import Sequence
from deeplabel.types.bounding_box import BoundingBoxWithNumber as BoundingBox
from deeplabel.types.polygon import Polygon


class DetectionType(Enum):
    BOUNDING_BOX='IMAGE_BOUNDING_BOX'
    POLYGON='IMAGE_POLYGON'
    CLASSIFICATION='IMAGE_CLASSIFICATION'


class Detection(DeeplabelBase):
    gallery_task_id: str
    image_id:str
    gallery_id:str
    probability: float
    graph_node_id:Optional[str]
    type:DetectionType = DetectionType.BOUNDING_BOX
    label: str = Field(alias="class")  # type: ignore
    sequence: Optional[Sequence] = None
    bounding_box: Optional[BoundingBox] = None
    polygon: Optional[Polygon] = None
    sub_class: List[str] = Field(default_factory=list)

    @classmethod
    def from_search_params(cls, params: Dict[str, Any], client: "deeplabel.client.BaseClient") -> List["Detection"]:  # type: ignore
        """Make a get request for detections using the passed params. This
        is a private method used internally by other class methods

        Returns:
            List[Detection]: Returns a list of Detection objects
        """
        detections = []
        if 'limit' in params and  (params['limit'] == -1 or params['limit'] == '-1'):
            page = 1
            limit = 500
            while True:
                params['limit'] = limit
                params['page'] = page
                resp = client.get("/image-detections", params=params)
                data = resp.json()["data"]["detections"]
                if not len(data):
                    break
                detections.extend(data)
                page += 1
        else:
            resp = client.get("/image-detections", params=params)
            detections = resp.json()["data"]["detections"]
        # don't check for empty list in this generic class method. returns empty list if no detections were found
        detections = [cls(**det,client=client) for det in detections]
        return detections #type: ignore

    @classmethod
    def from_detection_id(cls, detection_id: str, client: "deeplabel.client.BaseClient"):  # type: ignore
        """Get the Detection object for a certail detection_id

        Args:
            detection_id (str): detection Id to search for
            client (deeplabel.client.BaseClient): client to call the api from

        Raises:
            InvalidIdError: If no detections are returned, raise InvalidIdError

        Returns:
            Detection: returns a Detection object or raises InvalidIdError if not found
        """
        detections = cls.from_search_params({"detectionId": detection_id}, client)
        if not len(detections):
            raise InvalidIdError(
                f"Failed to fetch detections with detectionId  : {detection_id}"
            )
        # since detectionId should fetch only 1 detection, return that detection instead of a list
        return detections[0]

    @classmethod
    def from_gallery_task_id(
        cls, gallery_task_id: str, client: "deeplabel.client.BaseClient"
    ) -> List["Detection"]:
        """Get all the detection of a galleryTaskId

        Returns:
            List[Detection]: List of detections for the given galleryTaskId
        """
        return cls.from_search_params({"galleryTaskId": gallery_task_id}, client)

    # Below is the update method implemented by Sivaram, and then commented out by him.
    # Leaving it here as a reminder that the Detection.update is not needed to be in sdk

    # def update(self, detection_id: str, data: dict) -> dict:
    #     try:
    #         data["detectionId"] = detection_id
    #         data["restriction"] = False
    #         res = requests.put(self.detection_url,
    #                            json=data, headers=self.headers)
    #         detection = res.json()["data"]
    #         return detection
    #     except Exception as exc:
    #         print("update detection failed", exc)
