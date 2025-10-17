"""
Module to get videotasks data
"""
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional
import deeplabel.label.videos.detections
import deeplabel.client
from deeplabel.exceptions import InvalidIdError
from deeplabel.basemodel import DeeplabelBase, MixinConfig
from pydantic import Field
from logging import getLogger

logger = getLogger(__name__)


class VideoTaskStatus(Enum):
    TBD = "TBD"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    ABORTED = "ABORTED"
    FAILURE = "FAILURE"
    HOLD = "HOLD"


class videoId(MixinConfig):
    title: Optional[str]
    video_id: str


class Assignee(MixinConfig):
    name: str
    user_id: str

class ProjectId(MixinConfig):
    title: str
    project_id: str

class Timestamp(MixinConfig):
    created_at: Optional[datetime]
    modified_at: Optional[datetime]

class VideoTask(DeeplabelBase):
    video_task_id: str
    timestamp: Timestamp
    status: VideoTaskStatus
    dl_model_id:Optional[str]
    video: videoId = Field(..., alias='videoId')
    project: ProjectId = Field(..., alias='projectId')
    assignee: Assignee
    is_deleted: bool
    name: str

    @classmethod
    def from_search_params(cls, params: Dict[str, str], client: "deeplabel.client.BaseClient") -> List["VideoTask"]:  # type: ignore Used to ignore using private class BaseClient
        tasks = []
        if 'limit' in params and  (params['limit'] == -1 or params['limit'] == '-1'):
            page = 1
            limit = 500
            while True:
                params['limit'] = limit
                params['page'] = page
                resp = client.get("/projects/videos/tasks", params=params)
                data = resp.json()["data"]["videoTasks"]
                if not len(data):
                    break
                tasks.extend(data)
                page += 1
        else:
            resp = client.get("/projects/videos/tasks", params=params)
            tasks = resp.json()["data"]["videoTasks"]

        # Checkout https://lidatong.github.io/dataclasses-json/#use-my-dataclass-with-json-arrays-or-objects
        tasks = [cls(**task, client=client) for task in tasks]
        return tasks  # type: ignore

    @classmethod
    def from_video_task_id(
        cls, video_task_id: str, client: "deeplabel.client.BaseClient"
    ) -> "VideoTask":
        tasks = cls.from_search_params(
            params={"videoTaskId": video_task_id}, client=client
        )
        if not len(tasks):
            raise InvalidIdError(
                f"No VideoTask found for given video_task_id: {video_task_id}"
            )
        # since one videoTaskId corresponds to 1 and only 1 videoTask, return 0th videoTask
        return tasks[0]

    @classmethod
    def from_video_id(
        cls, video_id: str, client: "deeplabel.client.BaseClient"
    ) -> List["VideoTask"]:
        return cls.from_search_params({"videoId": video_id}, client)


    def update_status(
        self,
        status: VideoTaskStatus
        ):
        if status == self.status:
            raise ValueError(f"New Task Status cannot to same as current Task Status: {self.status.value}")
        data = {
            "videoTaskId": self.video_task_id,
            "status": status.value
        }

        updated_task = self.client.put("/projects/videos/tasks", json=data).json()["data"]
        setattr(self, "status", VideoTaskStatus(updated_task["status"]))
        return self
