import json
from deeplabel.basemodel import DeeplabelBase
from typing import Dict, Any, List, Union
import deeplabel.client
from deeplabel.exceptions import InvalidIdError
from pydantic import validator


class FeedbackConfig(DeeplabelBase):
    feedback_config_id: str
    name: str
    limit_per_video: int
    limit_per_folder: int
    selected_labels: List[str]
    project_id: str
    deleted_label_map: Union[str, Dict[str, Any]] = "{}"

    @validator("deleted_label_map")
    def validate_dicts(cls, v: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(v, dict):
            return v
        try:
            v = v.strip()
            if not v:
                v = "{}"
            v_ = json.loads(v)
            return v_
        except:
            raise ValueError(f"Failed to decode json.")

    @classmethod
    def from_search_params(
        cls, params: Dict[str, Any], client: "deeplabel.client.BaseClient"
    ) -> List["FeedbackConfig"]:
        resp = client.get("/feedback-config", params)
        configs = resp.json()["data"]["feedbackConfigs"]
        configs = [cls(**config, client=client) for config in configs]
        return configs  # type: ignore

    @classmethod
    def from_config_id(
        cls, config_id: str, client: "deeplabel.client.BaseClient"
    ) -> "FeedbackConfig":
        configs = cls.from_search_params({"feedbackConfigId": config_id}, client)
        if not configs:
            raise InvalidIdError(f"No Feedback config found with configId: {config_id}")
        return configs[0]


class GalleryFeedbackPipeline(DeeplabelBase):
    gallery_feedback_pipeline_id: str
    name: str
    project_id: str
    config_name: str
    config_id: str
    input_folder_ids: List[str]
    output_folder_id: str
    collate: bool = True  # Weather to maintain the folder hirarchy in feedback folder or put all galleries in one folder(i.e., collate the galleries)
    # labelling_fps: int = 5
    total_galleries: int = 0
    completed_galleries: int = 0
    failed_galleries: int = 0

    @classmethod
    def from_search_params(
        cls, params: Dict[str, Any], client: "deeplabel.client.BaseClient"
    ) -> List["GalleryFeedbackPipeline"]:
        resp = client.get("/gallery-feedback-pipeline", params)
        pipelines = resp.json()["data"]["feedbackPipelines"]
        pipelines = [cls(**pipeline, client=client) for pipeline in pipelines]
        return pipelines  # type: ignore

    @classmethod
    def from_pipeline_id(cls, pipeline_id: str, client: "deeplabel.client.BaseClient"):
        pipelines = cls.from_search_params({"galleryFeedbackPipelineId": pipeline_id}, client)
        if not pipelines:
            raise InvalidIdError(
                f"No Feedback Pipeline found with feedbackPipelineId: {pipeline_id}"
            )
        return pipelines[0]

    def increment_success_count(self):
        """increment the success_videos count in the db
        """
        resp = self.client.put( #type: ignore
            "/gallery-feedback-pipeline",
            {"pipelineId": self.gallery_feedback_pipeline_id, "success": True},
        )
        # self.completed_videos = resp['data']['completedVideos']

    def increment_failed_count(self):
        """Increment the failed_videos count in the db
        """
        resp = self.client.put( #type: ignore
            "/gallery-feedback-pipeline",
            {"pipelineId": self.gallery_feedback_pipeline_id, "success": False},
        )
        # self.failed_videos = resp['data']['failedVideos']

