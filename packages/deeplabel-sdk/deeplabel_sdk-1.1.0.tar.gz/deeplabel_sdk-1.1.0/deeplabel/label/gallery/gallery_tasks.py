"""
Module to get gallerytasks data
"""
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional
import deeplabel.client
from deeplabel.exceptions import InvalidIdError
from deeplabel.basemodel import DeeplabelBase, MixinConfig
from pydantic import Field
from logging import getLogger

logger = getLogger(__name__)


class GalleryTaskStatus(Enum):
    TBD = "TBD"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    ABORTED = "ABORTED"
    FAILURE = "FAILURE"


class galleryId(MixinConfig):
    title: Optional[str]
    gallery_id: str


class Assignee(MixinConfig):
    name: str
    user_id: str

class ProjectId(MixinConfig):
    title: str
    project_id: str

class Timestamp(MixinConfig):
    created_at: Optional[datetime]
    modified_at: Optional[datetime]

class GalleryTask(DeeplabelBase):
    gallery_task_id: str
    timestamp: Timestamp
    status: GalleryTaskStatus
    dl_model_id:Optional[str]
    gallery: galleryId = Field(..., alias='galleryId')
    project: ProjectId = Field(..., alias='projectId')
    assignee: Optional[Assignee]
    name: str

    @classmethod
    def from_search_params(cls, params: Dict[str, str], client: "deeplabel.client.BaseClient") -> List["GalleryTask"]:  # type: ignore Used to ignore using private class BaseClient
        tasks=[]
        if 'limit' in params and  (params['limit'] == -1 or params['limit'] == '-1'):
            page = 1
            limit = 500
            while True:
                params['limit'] = limit
                params['page'] = page
                resp = client.get("/projects/gallery/tasks", params=params)
                data = resp.json()["data"]["galleryTasks"]
                if not len(data):
                    break
                tasks.extend(data)
                page += 1
        else:
            resp = client.get("/projects/gallery/tasks", params=params)
            tasks = resp.json()["data"]["galleryTasks"]

        # Checkout https://lidatong.github.io/dataclasses-json/#use-my-dataclass-with-json-arrays-or-objects
        tasks = [cls(**task, client=client) for task in tasks]
        return tasks  # type: ignore

    @classmethod
    def from_gallery_task_id(
        cls, gallery_task_id: str, client: "deeplabel.client.BaseClient"
    ) -> "GalleryTask":
        tasks = cls.from_search_params(
            params={"galleryTaskId": gallery_task_id}, client=client
        )
        if not len(tasks):
            raise InvalidIdError(
                f"No GalleryTask found for given gallery_task_id: {gallery_task_id}"
            )
        # since one galleryTaskId corresponds to 1 and only 1 galleryTask, return 0th galleryTask
        return tasks[0]

    @classmethod
    def from_gallery_id(
        cls, gallery_id: str, client: "deeplabel.client.BaseClient"
    ) -> List["GalleryTask"]:
        return cls.from_search_params({"galleryId": gallery_id}, client)


    def update_status(
        self,
        status: GalleryTaskStatus
        ):
        if status == self.status:
            raise ValueError(f"New Task Status cannot to same as current Task Status: {self.status.value}")
        data = {
            "galleryTaskId": self.gallery_task_id,
            "status": status.value
        }

        updated_task = self.client.put("/projects/gallerys/tasks", json=data).json()["data"]
        setattr(self, "status", GalleryTaskStatus(updated_task["status"]))
        return self
