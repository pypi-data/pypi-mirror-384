from enum import Enum
from typing import List, Dict, Optional
import deeplabel.infer.graphs.graph_nodes
import deeplabel.infer.videos.video_tasks
import deeplabel.client
from deeplabel.exceptions import InvalidIdError
from deeplabel.basemodel import DeeplabelBase, MixinConfig
from pydantic import Field
from logging import getLogger

logger = getLogger(__name__)


class VideoGraphStatus(Enum):
    TBD = "TBD"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    ABORTED = "ABORTED"
    FAILURE = "FAILURE"


class VideoGraphVideoId(MixinConfig):
    title: Optional[str]
    video_id: str


class VideoGraphMode(Enum):
    PROD = "PROD"
    TEST = "TEST"


class AnnotatedVideoStatus(Enum):
    TBD = "TBD"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILURE"
    CANCELLED = "CANCELLED"
    ABORTED = "ABORTED"
    RETRY = "RETRY"


class AnnotatedVideo(MixinConfig):
    status: AnnotatedVideoStatus
    url: Optional[str] = None
    error_label: Optional[str] = None
    error_task: Optional[str] = None
    download_count: Optional[int] = 0


class VideoGraph(DeeplabelBase):
    video_graph_id: str
    video: VideoGraphVideoId = Field(..., alias="videoId")
    graph_id: str
    project_id: str
    status: VideoGraphStatus
    progress: int
    mode: Optional[VideoGraphMode] = VideoGraphMode.PROD
    annotated_video: Optional[AnnotatedVideo] = None

    @classmethod
    def create(
        cls,
        video_id: str,
        graph_id: str,
        mode: VideoGraphMode,
        client: "deeplabel.client.BaseClient",
    ) -> str:
        resp = client.post(
            "/videos/graphs",
            {
                "batch": True,
                "data": [
                    {"videoId": video_id, "graphId": graph_id, "mode": mode.value}
                ],
            },
        )
        return resp.json()["data"][0]["videoGraphId"]

    @classmethod
    def from_search_params(cls, params: Dict[str, str], client: "deeplabel.client.BaseClient") -> List["VideoGraph"]:  # type: ignore
        resp = client.get("/videos/graphs", params=params)
        videoGraphs = resp.json()["data"]["videoGraphs"]
        videoGraphs = [cls(**videoGraph, client=client) for videoGraph in videoGraphs]
        return videoGraphs  # type: ignore

    @classmethod
    def from_video_graph_id(
        cls, video_graph_id: str, client: "deeplabel.client.BaseClient"
    ) -> "VideoGraph":
        videoGraphs = cls.from_search_params(
            params={"videoGraphId": video_graph_id}, client=client
        )
        if not len(videoGraphs):
            raise InvalidIdError(
                f"No VideoGraph found for given video_graph_id: {video_graph_id}"
            )
        # since one videoTaskId corresponds to 1 and only 1 videoTask, return 0th videoTask
        return videoGraphs[0]

    @classmethod
    def from_video_id(
        cls, video_id: str, client: "deeplabel.client.BaseClient"
    ) -> List["VideoGraph"]:
        return cls.from_search_params({"videoId": video_id}, client)

    @property
    def video_tasks(self) -> List["deeplabel.infer.videos.video_tasks.VideoTask"]:
        """Get all the videoTasks for the given videoGraph

        Returns:
            List[deeplabel.infer.video_tasks.VideoTask]: duh, isn't that self explanatory?
        """
        return deeplabel.infer.videos.video_tasks.VideoTask.from_search_params(
            {
                "videoId": self.video.video_id,
                "graphId": self.graph_id,
                "projectId": self.project_id,
            },
            self.client,
        )

    def update_annotated_video(
        self, status: AnnotatedVideoStatus, url: Optional[str] = None
    ):
        request_data = {
            "videoGraphId": self.video_graph_id,
            "annotatedVideo": {"status": status.value},
        }
        if url is not None:
            request_data["annotatedVideo"]["url"] = url  # type: ignore

        resp = self.client.put("/videos/graphs/annotate", request_data)
        self.annotated_video = AnnotatedVideo(**resp.json()["data"]["annotatedVideo"])
