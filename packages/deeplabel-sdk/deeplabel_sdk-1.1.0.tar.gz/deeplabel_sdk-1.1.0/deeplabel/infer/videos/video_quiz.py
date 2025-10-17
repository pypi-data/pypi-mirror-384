"""
Module to get videoquiz data
"""
from typing import List, Dict, Optional, Any
from pydantic import conint
import deeplabel.client
from deeplabel.exceptions import InvalidIdError
from deeplabel.basemodel import DeeplabelBase, MixinConfig
from logging import getLogger
from enum import Enum

logger = getLogger(__name__)

class VideoQuizType(Enum):
    MCQ = "MCQ"

class _Option(MixinConfig):
    text: str
    is_correct: bool = False

class VideoQuiz(DeeplabelBase):
    video_quiz_id: str
    video_id: str
    project_id: str
    question: str
    context: str
    type: VideoQuizType
    options: List[_Option] = []
    display_time: int
    timeout: int = 5
    score: conint(ge=0, le=1) = 0
    parent_folder_id: Optional[str]
    ancestor_folder_ids: List[str] = []


    @classmethod
    def from_search_params(cls, params: Dict[str, str], client: "deeplabel.client.BaseClient") -> List["VideoQuiz"]:  # type: ignore Used to ignore using private class BaseClient
        resp = client.get("/video-quiz", params=params)
        quizes = resp.json()["data"]["videoQuiz"]
        quizes = [cls(**quiz, client=client) for quiz in quizes]
        return quizes  

    @classmethod
    def from_video_quiz_id(
        cls, video_quiz_id: str, client: "deeplabel.client.BaseClient"
    ) -> "VideoQuiz":
        quizes = cls.from_search_params(
            params={"videoQuizId": video_quiz_id}, client=client
        )
        if not len(quizes):
            raise InvalidIdError(
                f"No VideoQuiz found for given video_quiz_id: {video_quiz_id}"
            )
        return quizes[0]

    @classmethod
    def from_video_id(
        cls, video_id: str, client: "deeplabel.client.BaseClient"
    ) -> List["VideoQuiz"]:
        return cls.from_search_params({"videoId": video_id}, client)

    @classmethod
    def create(
        cls,
        video_id: str,
        data: Dict[str, Any],
        client: "deeplabel.client.BaseClient",
    ):
        
        resp = client.post(
            "/video-quiz",
            {"batch": True, "data": data, "videoId": video_id}
        )       

    @classmethod
    def update(
        cls,
        video_quiz_id: str,
        data: Dict[str, Any],
        client: "deeplabel.client.BaseClient",
    ):

        data['videoQuizId'] = video_quiz_id
        resp = client.put(f"/video-quiz", json=data)

    @classmethod
    def delete(
        cls,
        video_quiz_id: str,
        client: "deeplabel.client.BaseClient",
        hard_delete: bool = False

    ):

        data = {
            "videoQuizId": video_quiz_id,
            "hardDelete": hard_delete
        }
        resp = client.delete(f"/video-quiz", json=data)
   
