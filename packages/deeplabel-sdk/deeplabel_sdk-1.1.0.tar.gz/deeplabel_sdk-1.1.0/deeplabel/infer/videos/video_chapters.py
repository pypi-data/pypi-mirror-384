"""
Module to get videochapters data
"""
from typing import List, Dict, Optional, Any
import deeplabel.client
from deeplabel.exceptions import InvalidIdError
from deeplabel.basemodel import DeeplabelBase, MixinConfig
from logging import getLogger

logger = getLogger(__name__)

class VideoChapter(DeeplabelBase):
    video_chapter_id: str
    video_id: str
    project_id: str
    title: str
    sentences: List[str]
    start_time: int
    end_time: int
    parent_folder_id: Optional[str]
    ancestor_folder_ids: List[str] = []


    @classmethod
    def from_search_params(cls, params: Dict[str, str], client: "deeplabel.client.BaseClient") -> List["VideoChapter"]:  # type: ignore Used to ignore using private class BaseClient
        resp = client.get("/video-chapters", params=params)
        chapters = resp.json()["data"]["videoChapters"]
        chapters = [cls(**chapter, client=client) for chapter in chapters]
        return chapters  

    @classmethod
    def from_video_chapter_id(
        cls, video_chapter_id: str, client: "deeplabel.client.BaseClient"
    ) -> "VideoChapter":
        chapters = cls.from_search_params(
            params={"videoChapterId": video_chapter_id}, client=client
        )
        if not len(chapters):
            raise InvalidIdError(
                f"No VideoChapters found for given video_chapter_id: {video_chapter_id}"
            )
        return chapters[0]

    @classmethod
    def from_video_id(
        cls, video_id: str, client: "deeplabel.client.BaseClient"
    ) -> List["VideoChapter"]:
        return cls.from_search_params({"videoId": video_id}, client)

    @classmethod
    def create(
        cls,
        video_id: str,
        data: Dict[str, Any],
        client: "deeplabel.client.BaseClient",
    ):
        
        resp = client.post(
            "/video-chapters",
            {"batch": True, "data": data, "videoId": video_id}
        )       

    @classmethod
    def update(
        cls,
        video_chapter_id: str,
        data: Dict[str, Any],
        client: "deeplabel.client.BaseClient",
    ):

        data['videoChapterId'] = video_chapter_id
        resp = client.put(f"/video-chapters", json=data)

    @classmethod
    def delete(
        cls,
        video_chapter_id: str,
        client: "deeplabel.client.BaseClient",
        hard_delete: bool = False

    ):

        data = {
            "videoChapterId": video_chapter_id,
            "hardDelete": hard_delete
        }
        resp = client.delete(f"/video-chapters", json=data)