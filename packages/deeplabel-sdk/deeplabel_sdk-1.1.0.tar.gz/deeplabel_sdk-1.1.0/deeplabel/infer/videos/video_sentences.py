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

class VideoSentence(DeeplabelBase):
    video_sentence_id: str
    video_id: str
    project_id: str
    text: str
    start_time: int
    end_time: int
    parent_folder_id: Optional[str]
    ancestor_folder_ids: List[str] = []


    @classmethod
    def from_search_params(cls, params: Dict[str, str], client: "deeplabel.client.BaseClient") -> List["VideoSentence"]:  # type: ignore Used to ignore using private class BaseClient
        resp = client.get("/video-sentences", params=params)
        sentences = resp.json()["data"]["videoSentences"]
        sentences = [cls(**sentence, client=client) for sentence in sentences]
        return sentences  

    @classmethod
    def from_video_sentence_id(
        cls, video_sentence_id: str, client: "deeplabel.client.BaseClient"
    ) -> "VideoSentence":
        sentences = cls.from_search_params(
            params={"videoSentenceId": video_sentence_id}, client=client
        )
        if not len(sentences):
            raise InvalidIdError(
                f"No VideoSentence found for given video_sentence_id: {video_sentence_id}"
            )
        return sentences[0]

    @classmethod
    def from_video_id(
        cls, video_id: str, client: "deeplabel.client.BaseClient"
    ) -> List["VideoSentence"]:
        return cls.from_search_params({"videoId": video_id}, client)

    @classmethod
    def create(
        cls,
        video_id: str,
        data: Dict[str, Any],
        client: "deeplabel.client.BaseClient",
    ):
        
        resp = client.post(
            "/video-sentences",
            {"batch": True, "data": data, "videoId": video_id}
        )       

    @classmethod
    def update(
        cls,
        video_sentence_id: str,
        data: Dict[str, Any],
        client: "deeplabel.client.BaseClient",
    ):

        data['videoSentenceId'] = video_sentence_id
        resp = client.put(f"/video-sentences", json=data)

    @classmethod
    def delete(
        cls,
        video_sentence_id: str,
        client: "deeplabel.client.BaseClient",
        hard_delete: bool = False

    ):

        data = {
            "videoSentenceId": video_sentence_id,
            "hardDelete": hard_delete
        }
        resp = client.delete(f"/video-sentences", json=data)
   
