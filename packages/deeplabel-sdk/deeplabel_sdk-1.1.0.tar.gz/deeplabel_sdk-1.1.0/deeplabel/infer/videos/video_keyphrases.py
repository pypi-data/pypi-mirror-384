"""
Module to get vidoekeyphrases data
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

class VideoKeyphrase(DeeplabelBase):
    video_keyphrase_id: str
    video_id: str
    project_id: str
    text: str
    time_instances: List[_TimeInstance]
    parent_folder_id: Optional[str]
    ancestor_folder_ids: List[str] = []


    @classmethod
    def from_search_params(cls, params: Dict[str, str], client: "deeplabel.client.BaseClient") -> List["VideoKeyphrase"]:  # type: ignore Used to ignore using private class BaseClient
        resp = client.get("/video-keyphrases", params=params)
        keyphrases = resp.json()["data"]["videoKeyphrases"]
        keyphrases = [cls(**keyphrase, client=client) for keyphrase in keyphrases]
        return keyphrases  

    @classmethod
    def from_video_keyphrase_id(
        cls, video_keyphrase_id: str, client: "deeplabel.client.BaseClient"
    ) -> "VideoKeyphrase":
        keyphrases = cls.from_search_params(
            params={"videoKeyphraseId": video_keyphrase_id}, client=client
        )
        if not len(keyphrases):
            raise InvalidIdError(
                f"No VideoKeyphrases found for given video_keyphrase_id: {video_keyphrase_id}"
            )
        return keyphrases[0]

    @classmethod
    def from_video_id(
        cls, video_id: str, client: "deeplabel.client.BaseClient"
    ) -> List["VideoKeyphrase"]:
        return cls.from_search_params({"videoId": video_id}, client)

    @classmethod
    def create(
        cls,
        video_id: str,
        data: Dict[str, Any],
        client: "deeplabel.client.BaseClient",
    ):
        
        resp = client.post(
            "/video-keyphrases",
            {"batch": True, "data": data, "videoId": video_id}
        )       

    @classmethod
    def update(
        cls,
        video_keyphrase_id: str,
        data: Dict[str, Any],
        client: "deeplabel.client.BaseClient",
    ):

        data['videoKeyphraseId'] = video_keyphrase_id
        resp = client.put(f"/video-keyphrases", json=data)

    @classmethod
    def delete(
        cls,
        video_keyphrase_id: str,
        client: "deeplabel.client.BaseClient",
        hard_delete: bool = False

    ):

        data = {
            "videoKeyphraseId": video_keyphrase_id,
            "hardDelete": hard_delete
        }
        resp = client.delete(f"/video-keyphrases", json=data)