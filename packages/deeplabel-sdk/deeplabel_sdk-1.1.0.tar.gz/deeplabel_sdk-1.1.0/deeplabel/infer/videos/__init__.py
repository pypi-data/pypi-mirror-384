"""
Module to get videos data
"""
from typing import Any, Dict, List, Optional
import deeplabel.client
import deeplabel
from deeplabel.exceptions import InvalidIdError
import deeplabel.infer.videos.video_tasks
import deeplabel.infer.videos.video_graphs
from deeplabel.basemodel import DeeplabelBase, MixinConfig
from urllib.parse import urlparse, parse_qs
import requests
import time
from pydantic import Field, validator
from enum import Enum

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

class VttType(Enum):
    DEFAULT = 'DEFAULT'
    AUTO = 'AUTO'
    GCP = 'GCP'
class Video(DeeplabelBase):
    video_id: str
    project_id:str
    input_url: str
    parent_folder_id: Optional[str]
    ancestor_folder_ids: List[str] = []
    video_urls: Optional[_VideoUrl]
    video_fps: Optional[float] = None
    duration: Optional[float] = None  # in seconds
    title: Optional[str] = ''
    vtt_url: Optional[str] 
    vtt_type: Optional[VttType] 


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
        # if expiry is more that now + 5 mins. don't update
        if expiry_key and int(query[expiry_key][0]) > int(time.time()) + 300:
            return url
        # if presigned url that is expired
        # or is about to expire or
        # doesn't has a video_url
        # or head request fails
        elif expiry_key or (not url or requests.head(url).status_code != 200):
            video = self._generate_video_url(self.video_id, self.client)
            self.video_urls = video.video_urls
            return self.video_urls.source.url #type: ignore # since this api will always return a valid source.url
        return url

    @staticmethod
    def _generate_video_url(video_id:str, client:"deeplabel.client.BaseClient"):
        resp = client.get('/videos/video-url', params={"videoId":video_id})
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
                resp = client.get("/videos", params=params)
                data = resp.json()["data"]["videos"]
                if not len(data):
                    break
                videos.extend(data)
                page += 1
        else:
            resp = client.get("/videos", params=params)
            videos = resp.json()["data"]["videos"]

        videos = [cls(**video, client=client) for video in videos]
        return videos  # type: ignore

    @classmethod
    def create(
        cls,
        input_url: str,
        project_id: str,
        client: "deeplabel.client.BaseClient",
        parent_folder_id: Optional[str] = None,
    ) -> str:
        """Create a video and return the videoId"""
        resp = client.post(
            "/videos",
            {
                "inputUrl": input_url,
                "projectId": project_id,
                "parentFolderId": parent_folder_id,
            },
        )
        video_id = resp.json()["data"]["videoId"]
        # fetch again so that the videoUrl is set
        # return cls.from_video_id(video_id, client)
        return video_id
    
    @classmethod
    def update(
        cls,
        video_id: str,
        data: Dict[str, Any],
        client: "deeplabel.client.BaseClient",
    ):
        """Update a video and return the videoId"""
        data['videoId'] = video_id
        resp = client.put("/videos",data)
        video_id = resp.json()["data"]["videoId"]
        return video_id

    @classmethod
    def from_video_id(
        cls, video_id: str, client: "deeplabel.client.BaseClient"
    ) -> "Video":
        video = cls.from_search_params({"videoId": video_id}, client=client)
        if not len(video):
            raise InvalidIdError(f"Failed to fetch video with videoId: {video_id}")
        return video[0]

    @classmethod
    def from_folder_id(
        cls, folder_id: str, client: "deeplabel.client.BaseClient"
    ) -> List["Video"]:
        return cls.from_search_params({"parentFolderId": folder_id}, client)

    @property
    def video_tasks(self) -> List["deeplabel.infer.videos.video_tasks.VideoTask"]:
        return deeplabel.infer.videos.video_tasks.VideoTask.from_video_id(
            self.video_id, self.client
        )
    
    @property
    def video_graphs(self) -> List['deeplabel.infer.videos.video_graphs.VideoGraph']:
        return deeplabel.infer.videos.video_graphs.VideoGraph.from_video_id(
            video_id = self.video_id, client = self.client
        )

    def update_metadata(self, data: Dict[str, Any]) -> "Video":
        """Update metadata of this video and return new Video object from it
        Since update might not work for all fields, do check in the returned
        Video object if the desired change has taken effect.

        Returns:
            Video: New Video object of the returned data
        """
        data["videoId"] = self.video_id
        res = self.client.put("/videos/metadata", json=data)
        video = res.json()["data"]
        return Video(**video)
