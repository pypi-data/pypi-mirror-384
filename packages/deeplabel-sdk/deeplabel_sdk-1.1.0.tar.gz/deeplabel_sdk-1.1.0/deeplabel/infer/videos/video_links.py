"""
Module to get videolinks data
"""
from typing import List, Dict, Optional, Any
import deeplabel.client
from deeplabel.exceptions import InvalidIdError
from deeplabel.basemodel import DeeplabelBase, MixinConfig
from logging import getLogger

logger = getLogger(__name__)


class VideoLink(DeeplabelBase):
    video_link_id: str
    video_id: str
    project_id: str
    video_keyphrase_id: str
    title: str
    link: str
    description: Optional[str]
    parent_folder_id: Optional[str]
    ancestor_folder_ids: List[str] = []


    @classmethod
    def from_search_params(cls, params: Dict[str, str], client: "deeplabel.client.BaseClient") -> List["VideoLink"]:  # type: ignore Used to ignore using private class BaseClient
        resp = client.get("/video-links", params=params)
        links = resp.json()["data"]["videoLinks"]
        links = [cls(**Link, client=client) for Link in links]
        return links  

    @classmethod
    def from_video_link_id(
        cls, video_link_id: str, client: "deeplabel.client.BaseClient"
    ) -> "VideoLink":
        links = cls.from_search_params(
            params={"videoLinkId": video_link_id}, client=client
        )
        if not len(links):
            raise InvalidIdError(
                f"No Videolinks found for given video_link_id: {video_link_id}"
            )
        return links[0]

    @classmethod
    def from_video_id(
        cls, video_id: str, client: "deeplabel.client.BaseClient"
    ) -> List["VideoLink"]:
        return cls.from_search_params({"videoId": video_id}, client)
    
    @classmethod
    def create(
        cls,
        video_id: str,
        data: Dict[str, Any],
        client: "deeplabel.client.BaseClient",
    ):
        
        resp = client.post(
            "/video-links",
            {"batch": True, "data": data, "videoId": video_id}
        )       

    @classmethod
    def update(
        cls,
        video_Link_id: str,
        data: Dict[str, Any],
        client: "deeplabel.client.BaseClient",
    ):

        data['videoLinkId'] = video_Link_id
        resp = client.put(f"/video-links", json=data)

    @classmethod
    def delete(
        cls,
        video_Link_id: str,
        client: "deeplabel.client.BaseClient",
        hard_delete: bool = False

    ):

        data = {
            "videoLinkId": video_Link_id,
            "hardDelete": hard_delete
        }
        resp = client.delete(f"/video-links", json=data)
   
