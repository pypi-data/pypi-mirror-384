"""
Module to get videosentence data
"""
from typing import List, Dict, Optional, Any
from pydantic import conint
import deeplabel.client
from deeplabel.exceptions import InvalidIdError
from deeplabel.basemodel import DeeplabelBase, MixinConfig
from logging import getLogger
from enum import Enum

logger = getLogger(__name__)

class VideoSummaryType(Enum):
    ABSTRACTIVE = "ABSTRACTIVE"
    EXTRACTIVE = "EXTRACTIVE"

class VideoSummary(DeeplabelBase):
    video_summary_id: str
    video_id: str
    project_id: str
    text: str
    type: VideoSummaryType
    parent_folder_id: Optional[str]
    ancestor_folder_ids: List[str] = []


    @classmethod
    def from_search_params(cls, params: Dict[str, str], client: "deeplabel.client.BaseClient") -> List["VideoSummary"]:  # type: ignore Used to ignore using private class BaseClient
        resp = client.get("/video-summary", params=params)
        summaries = resp.json()["data"]["videoSummary"]
        summaries = [cls(**summary, client=client) for summary in summaries]
        return summaries  

    @classmethod
    def from_video_summary_id(
        cls, video_summary_id: str, client: "deeplabel.client.BaseClient"
    ) -> "VideoSummary":
        summaries = cls.from_search_params(
            params={"videoSummaryId": video_summary_id}, client=client
        )
        if not len(summaries):
            raise InvalidIdError(
                f"No VideoSummary found for given video_summary_id: {video_summary_id}"
            )
        return summaries[0]

    @classmethod
    def from_video_id(
        cls, video_id: str, client: "deeplabel.client.BaseClient"
    ) -> List["VideoSummary"]:
        return cls.from_search_params({"videoId": video_id}, client)

   
    @classmethod
    def create(
        cls,
        video_id: str,
        data: Dict[str, Any],
        client: "deeplabel.client.BaseClient",
    ):
        
        resp = client.post(
            "/video-summary",
            {"batch": True, "data": data, "videoId": video_id}
        )       

    @classmethod
    def update(
        cls,
        video_summary_id: str,
        data: Dict[str, Any],
        client: "deeplabel.client.BaseClient",
    ):

        data['videoSummaryId'] = video_summary_id
        resp = client.put(f"/video-summary", json=data)

    @classmethod
    def delete(
        cls,
        video_summary_id: str,
        client: "deeplabel.client.BaseClient",
        hard_delete: bool = False

    ):

        data = {
            "videoSummaryId": video_summary_id,
            "hardDelete": hard_delete
        }
        resp = client.delete(f"/video-summary", json=data)
   
