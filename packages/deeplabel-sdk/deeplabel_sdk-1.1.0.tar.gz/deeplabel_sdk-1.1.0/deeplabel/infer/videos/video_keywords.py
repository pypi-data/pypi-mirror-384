"""
Module to get videokeywords data
"""
from typing import List, Dict, Optional, Any
import deeplabel.client
from deeplabel.exceptions import InvalidIdError
from deeplabel.basemodel import DeeplabelBase, MixinConfig
from logging import getLogger

logger = getLogger(__name__)

class _TimeInstance(MixinConfig):
    start_time: int
    end_time: int

class _KeyPhrase(MixinConfig):
    text: str
    time_instances: List[_TimeInstance]

class VideoKeyword(DeeplabelBase):
    video_keyword_id: str
    video_id: str
    project_id: str
    text: str
    keyphrases: List[_KeyPhrase]
    time_instances: List[_TimeInstance]
    chapter_ids: List[str] = []
    parent_folder_id: Optional[str]
    ancestor_folder_ids: List[str] = []


    @classmethod
    def from_search_params(cls, params: Dict[str, str], client: "deeplabel.client.BaseClient") -> List["VideoKeyword"]:  # type: ignore Used to ignore using private class BaseClient
        resp = client.get("/video-keywords", params=params)
        keywords = resp.json()["data"]["videoKeywords"]
        keywords = [cls(**keyword, client=client) for keyword in keywords]
        return keywords  

    @classmethod
    def from_video_keyword_id(
        cls, video_keyword_id: str, client: "deeplabel.client.BaseClient"
    ) -> "VideoKeyword":
        keywords = cls.from_search_params(
            params={"videoKeywordId": video_keyword_id}, client=client
        )
        if not len(keywords):
            raise InvalidIdError(
                f"No VideoKeywords found for given video_keyword_id: {video_keyword_id}"
            )
        return keywords[0]

    @classmethod
    def from_video_id(
        cls, video_id: str, client: "deeplabel.client.BaseClient"
    ) -> List["VideoKeyword"]:
        return cls.from_search_params({"videoId": video_id}, client)
    
    @classmethod
    def create(
        cls,
        video_id: str,
        data: Dict[str, Any],
        client: "deeplabel.client.BaseClient",
    ):
        
        resp = client.post(
            "/video-keywords",
            {"batch": True, "data": data, "videoId": video_id}
        )       

    @classmethod
    def update(
        cls,
        video_keyword_id: str,
        data: Dict[str, Any],
        client: "deeplabel.client.BaseClient",
    ):

        data['videoKeywordId'] = video_keyword_id
        resp = client.put(f"/video-keywords", json=data)

    @classmethod
    def delete(
        cls,
        video_keyword_id: str,
        client: "deeplabel.client.BaseClient",
        hard_delete: bool = False

    ):

        data = {
            "videoKeywordId": video_keyword_id,
            "hardDelete": hard_delete
        }
        resp = client.delete(f"/video-keywords", json=data)
   
