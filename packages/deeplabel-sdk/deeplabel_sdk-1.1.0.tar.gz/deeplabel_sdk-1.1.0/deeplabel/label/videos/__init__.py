"""
Module to get videos data
"""
from enum import Enum
import time
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
from pydantic import Field
from deeplabel.basemodel import DeeplabelBase, MixinConfig
import deeplabel.label.videos.frames
import deeplabel.label.videos.detections
import deeplabel.label.videos.video_tasks
import deeplabel.client
from deeplabel.exceptions import InvalidIdError
import yarl
import os
from deeplabel.exceptions import DeeplabelValueError
from logging import getLogger

logger = getLogger(__name__)


class _VideoResolution(MixinConfig):
    height: int
    width: int


class _VideoFormat(MixinConfig):
    url: str
    resolution: Optional[_VideoResolution] = None
    extension: Optional[str] = None
    fps: Optional[float] = None
    file_size: Optional[float] = None


class _VideoUrl(MixinConfig):
    source: Optional[_VideoFormat]
    res360: Optional[_VideoFormat] = Field(None, alias="360P")
    res480: Optional[_VideoFormat] = Field(None, alias="480P")
    res720: Optional[_VideoFormat] = Field(None, alias="720P")
    res1080: Optional[_VideoFormat] = Field(None, alias="1080P")
    res1440: Optional[_VideoFormat] = Field(None, alias="1440P")
    res2160: Optional[_VideoFormat] = Field(None, alias="2160P")


class _TaskStatus(Enum):
    TBD = "TBD"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    CANCELLED = "CANCELLED"
    ABORTED = "ABORTED"
    HOLD = "HOLD"
    RETRY = "RETRY"
    REDO = "REDO"


class _BaseStatus(MixinConfig):
    status: _TaskStatus
    start_time: float
    end_time: float
    error: Optional[str] = None


class _InferenceStatus(_BaseStatus):
    dl_model_id: Optional[str]
    progress: float


class _LabelVideoStatus(MixinConfig):
    download: _BaseStatus
    assign_resources: _BaseStatus
    extraction: _BaseStatus
    frames_extraction: _BaseStatus
    inference: _InferenceStatus
    label: _BaseStatus
    review: _BaseStatus
    labelling: _BaseStatus


class ExtractionPoint(MixinConfig):
    labelling_fps: int
    start_time: float
    end_time: float


class Video(DeeplabelBase):
    video_id: str
    title: Optional[str]
    project_id: str
    input_url: str
    video_urls: Optional[_VideoUrl]
    thumbnail_url: Optional[str]
    status: _LabelVideoStatus
    extraction_points: List[ExtractionPoint]
    duration: Optional[float]
    video_fps: Optional[float]
    labelling_fps: int
    is_feedback: bool = False

    @classmethod
    def create(
        cls,
        input_url: str,
        project_id: str,
        client: "deeplabel.client.BaseClient",
        parent_folder_id: Optional[str] = None,
        is_feedback: bool = False,
    ) -> str:
        """Create a video and return the video"""
        resp = client.post(
            "/projects/videos",
            {
                "inputUrl": input_url,
                "projectId": project_id,
                "parentFolderId": parent_folder_id,
                "isFeedback": is_feedback,
            },
        )
        video_id = resp.json()["data"]["videoId"]
        # fetch again so that the videoUrl is set
        # return cls.from_video_id(video_id, client)
        return video_id

    @property
    def video_url(self) -> str:
        """This API generates a new presigned video url incase the old one has expired"""
        if self.video_urls is not None:
            url = self.video_urls.source.url
        else:
            url = self.extra.get('video_url', '')

        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        expiry_key:Optional[str] = None
        for key in query.keys():
            if key.lower().startswith('expire'):
                expiry_key = key
                break
        # if expiry is more that now + 30 sec. don't update
        if expiry_key and int(query[expiry_key][0]) > int(time.time()) + 30:
            return url
        # if presigned url that is expired
        # or is about to expire or
        # doesn't has a video_url
        # or head request fails
        elif expiry_key or (not url or self.client.session.head(url).status_code != 200):
            video = self._generate_video_url(self.video_id, self.client)
            self.video_urls = video.video_urls
            return self.video_urls.source.url #type: ignore # since this api will always return a valid source.url
        return url

    @staticmethod
    def _generate_video_url(video_id:str, client:"deeplabel.client.BaseClient"):
        resp = client.get('/projects/videos/video-url', params={"videoId":video_id})
        video = Video(**resp.json()['data']['videos'][0])
        return video

    @classmethod
    def from_search_params(
        cls, params: Dict[str, Any], client: "deeplabel.client.BaseClient"
    ) -> List["Video"]:
        videos = []
        if 'limit' in params and (params['limit'] == -1 or params['limit'] == '-1'):
            page = 1
            limit = 500
            while True:
                params['limit'] = limit
                params['page'] = page
                resp = client.get("/projects/videos", params=params)
                data = resp.json()["data"]["videos"]
                if not len(data):
                    break
                videos.extend(data)
                page += 1
        else:
            resp = client.get("/projects/videos", params=params)
            videos = resp.json()["data"]["videos"]
        videos = [cls(**video, client=client) for video in videos]
        return videos  # type: ignore

    @classmethod
    def from_video_id(
        cls, video_id: str, client: "deeplabel.client.BaseClient"
    ) -> "Video":
        videos = cls.from_search_params({"videoId": video_id}, client)
        if not len(videos):
            raise InvalidIdError(f"Failed to fetch video with videoId  : {video_id}")
        # since videoId should fetch only 1 video, return that video instead of a list
        return videos[0]

    @property
    def ext(self):
        """Extenion of the video, deduced from path/name"""
        return os.path.splitext(yarl.URL(self.video_url).name)[-1]  # type: ignore

    @property
    def detections(self):
        """Get Detections of the video"""
        return deeplabel.label.videos.detections.Detection.from_video_id_and_project_id(
            self.video_id, self.project_id, self.client
        )

    @property
    def frames(self):
        """Get Detections of the video"""
        return deeplabel.label.videos.frames.Frame.from_video_and_project_id(
            self.video_id, self.project_id, self.client
        )

    @property
    def tasks(self):
        """Get tasks of the video"""
        return deeplabel.label.videos.video_tasks.VideoTask.from_video_id(
            self.video_id, self.client
        )

    def get_task_by_name(
        self, task_name: str
    ) -> Optional["deeplabel.label.videos.video_tasks.VideoTask"]:
        tasks = deeplabel.label.videos.video_tasks.VideoTask.from_search_params(
            {"name": task_name, "videoId": self.video_id, "projectId": self.project_id},
            self.client,
        )
        if not tasks:
            return None
        return tasks[0]

    def set_extraction_timepoints(self, extraction_timepoints: List[ExtractionPoint]):
        extraction_task = self.get_task_by_name("EXTRACTION")
        # IF extraction task doesn't exist or is not in progress
        if (
            extraction_task is None
            or extraction_task.status
            != deeplabel.label.videos.video_tasks.VideoTaskStatus.IN_PROGRESS
        ):
            raise ValueError(
                f"Extraction Task for VideoId {self.video_id} is not IN_PROGRESS"
            )

        resp = self.client.put(
            "/projects/videos/extractions",
            {
                "videoId": self.video_id,
                "extractionPoints": [
                    point.dict(by_alias=True, exclude_none=True)
                    for point in extraction_timepoints
                ],
            },  # type: ignore
        )
        if resp.status_code > 400:
            raise DeeplabelValueError(
                f"Failed inserting extraction timepoints for videoId {self.video_id} with IN_PROGRESS EXTRACTION task {extraction_task.video_task_id}: {resp.json()}"
            )

    def insert_detections(
        self,
        detections: List["deeplabel.label.videos.detections.Detection"],
        chunk_size: int = 500,
    ):
        DetectionType = deeplabel.label.videos.detections.DetectionType
        label_task = self.get_task_by_name("LABEL")
        if (
            label_task is None
            or label_task.status
            != deeplabel.label.videos.video_tasks.VideoTaskStatus.IN_PROGRESS
        ):
            raise ValueError(
                f"LABEL Task for VideoId {self.video_id} is not IN_PROGRESS"
            )
        logger.info(f"Inserting {len(detections)} for video {self.video_id}")

        i = 0
        while i * chunk_size < len(detections):
            request_detections:List[Dict[str, Any]] = []
            for detection in detections[chunk_size * i : chunk_size * (i + 1)]:
                det = {
                    "labelId": detection.label.label_id,
                    "type": detection.type.value,
                    "frameId": detection.frame_id
                }
                if detection.type == DetectionType.BOUNDING_BOX:
                    det["boundingBox"] = detection.bounding_box.dict( #type: ignore
                        exclude_defaults=True, exclude_none=True
                    )
                if detection.type == DetectionType.POLYGON:
                    det["polygon"] = detection.polygon.dict()  # type: ignore
                request_detections.append(det)
            request_data = {
                "batch": True,
                "data": request_detections,
            }
            resp = self.client.post("/projects/videos/frames/detections", request_data)
            if resp.status_code > 400:
                raise DeeplabelValueError(
                    f"Failed inserting detections for videoId {self.video_id} with IN_PROGRESS LABEL task {label_task.video_task_id}: {resp.json()}"
                )
            i += 1
