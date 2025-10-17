from enum import Enum
from typing import List, Optional, Dict, Any
from deeplabel.basemodel import DeeplabelBase, MixinConfig
import deeplabel.label.gallery.images
from deeplabel.label.gallery.gallery_tasks import GalleryTask
import deeplabel.client
from deeplabel.exceptions import InvalidAPIResponse, InvalidIdError
import logging

logger = logging.getLogger(__name__)


class _TaskStatus(Enum):
    TBD = "TBD"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    CANCELLED = "CANCELLED"
    ABORTED = "ABORTED"
    HOLD = "HOLD"


class _BaseStatus(MixinConfig):
    status: _TaskStatus
    start_time: float
    end_time: float
    error: Optional[str] = None


class _InferenceStatus(_BaseStatus):
    dl_model_id: Optional[str]
    progress: float


class _LabelGalleryStatus(MixinConfig):
    submit: _BaseStatus
    assign_resources: _BaseStatus
    inference: _InferenceStatus
    label: _BaseStatus
    review: _BaseStatus
    labelling: _BaseStatus


class Gallery(DeeplabelBase):
    gallery_id: str
    title:str
    description:str
    is_deleted:bool
    parent_folder_id:Optional[str]
    project_id: str
    owner_id: str
    status: _LabelGalleryStatus
    is_feedback:bool = False

    @classmethod
    def from_search_params(
        cls, params: Dict[str, Any], client: "deeplabel.client.BaseClient"
    ) -> List["Gallery"]:
        galleries = []
        if 'limit' in params and  (params['limit'] == -1 or params['limit'] == '-1'):
            page = 1
            limit = 500
            while True:
                params['limit'] = limit
                params['page'] = page
                resp = client.get("/projects/gallery", params=params)
                data = resp.json()["data"]["gallery"]
                if not len(data):
                    break
                galleries.extend(data)
                page += 1
        else:
            resp = client.get("/projects/gallery", params=params)
            galleries = resp.json()["data"]["gallery"]
        galleries = [cls(**gallery, client=client) for gallery in galleries]
        return galleries  # type:ignore

    @classmethod
    def from_gallery_id(
        cls, gallery_id: str, client: "deeplabel.client.BaseClient"
    ) -> "Gallery":
        galleries = cls.from_search_params({"galleryId": gallery_id}, client)
        if not len(galleries):
            raise InvalidIdError(
                f"Failed to fetch gallery with galleryId  : {gallery_id}"
            )
        # since galleryId should fetch only 1 gallery, return that gallery instead of a list
        return galleries[0]

    @property
    def images(self) -> List["deeplabel.label.gallery.images.Image"]:
        """Get Images of the Gallery"""
        return deeplabel.label.gallery.images.Image.from_gallery_and_project_id(
            self.gallery_id, self.project_id, self.client
        )

    @classmethod
    def create(
        cls,
        title: str,
        project_id: str,
        parent_folder_id: Optional[str],
        client: "deeplabel.client.BaseClient",
        is_feedback: bool = False,
    ) -> "Gallery":
        resp = client.post(
            "/projects/gallery",
            {
                "projectId": project_id,
                "parentFolderId": parent_folder_id,
                "title": title,
                "isFeedback":is_feedback,
            },
        )
        if resp.status_code == 200:
            gallery = cls(**resp.json()["data"], client=client)
            logger.info(f"Gallery Created: {gallery.title} {gallery.gallery_id}")
            return gallery
        else:
            logger.error(f"Failed creating gallery")
            raise InvalidAPIResponse(resp.text)

    def submit_for_labelling(self):
        resp = self.client.post(
            "/projects/gallery/tasks",
            {
                "galleryId": self.gallery_id,
                "name": "SUBMIT",
                "status": "SUCCESS",
            },
        )
        if resp.status_code > 200:
            logger.error(f"Failed submitting the gallery for labelling. {resp.text}")
            raise ValueError(
                f"Failed submitting gallery {self.gallery_id} for labelling. {resp.text}"
            )
        else:
            logger.info(
                f"Gallery {self.title} {self.gallery_id} submitted for labelling"
            )

    @property
    def tasks(self) -> List["GalleryTask"]:
        self.client: "deeplabel.client.BaseClient"
        return GalleryTask.from_search_params(
            {"galleryId": self.gallery_id}, self.client
        )
