from enum import Enum
from typing import List, Dict, Optional
import deeplabel.infer.graphs.graph_nodes
import deeplabel.infer.gallery.gallery_tasks
import deeplabel.client
from deeplabel.exceptions import InvalidIdError
from deeplabel.basemodel import DeeplabelBase, MixinConfig
from pydantic import Field
from logging import getLogger

logger = getLogger(__name__)

class GalleryGraphStatus(Enum):
    TBD = "TBD"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    ABORTED = "ABORTED"
    FAILURE = "FAILURE"


class GalleryGraphGalleryId(MixinConfig):
    title: Optional[str]
    gallery_id: str


class GalleryGraphMode(Enum):
    PROD = "PROD"
    TEST = "TEST"


class AnnotatedGalleryStatus(Enum):
    TBD = "TBD"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILURE"
    CANCELLED = "CANCELLED"
    ABORTED = "ABORTED"
    RETRY = "RETRY"


class AnnotatedGallery(MixinConfig):
    status: AnnotatedGalleryStatus
    url: Optional[str] = None
    error_label: Optional[str] = None
    error_task: Optional[str] = None
    download_count: Optional[int] = 0


class GalleryGraph(DeeplabelBase):
    gallery_graph_id: str
    gallery:  GalleryGraphGalleryId= Field(..., alias="galleryId")
    graph_id: str
    project_id: str
    status: GalleryGraphStatus
    progress: int
    mode: Optional[GalleryGraphMode] = GalleryGraphMode.PROD
    annotated_gallery: Optional[AnnotatedGallery] = None

    @classmethod
    def create(
        cls,
        gallery_id: str,
        graph_id: str,
        mode: GalleryGraphMode,
        client: "deeplabel.client.BaseClient",
    ) -> str:
        resp = client.post(
            "/gallery/graphs",
            {
                "batch": True,
                "data": [
                    {"galleryId": gallery_id, "graphId": graph_id, "mode": mode.value}
                ],
            },
        )
        return resp.json()["data"][0]["galleryGraphId"]

    @classmethod
    def from_search_params(cls, params: Dict[str, str], client: "deeplabel.client.BaseClient") -> List["GalleryGraph"]:  # type: ignore
        resp = client.get("/gallery/graphs", params=params)
        galleryGraphs = resp.json()["data"]["galleryGraphs"]
        galleryGraphs = [cls(**galleryGraph, client=client) for galleryGraph in galleryGraphs]
        return galleryGraphs  # type: ignore

    @classmethod
    def from_gallery_graph_id(
        cls, gallery_graph_id: str, client: "deeplabel.client.BaseClient"
    ) -> "GalleryGraph":
        galleryGraphs = cls.from_search_params(
            params={"galleryGraphId":gallery_graph_id}, client=client
        )
        if not len(galleryGraphs):
            raise InvalidIdError(
                f"No Gallery graphs found for given gallery_graph_id: {gallery_graph_id}"
            )
        # since one galleryTaskId corresponds to 1 and only 1 galleryTask, return 0th galleryTask
        return galleryGraphs[0]

    @classmethod
    def from_gallery_id(
        cls, gallery_id: str, client: "deeplabel.client.BaseClient"
    ) -> List["GalleryGraph"]:
        return cls.from_search_params({"galleryId": gallery_id}, client)

    @property
    def gallery_tasks(self) -> List["deeplabel.infer.gallery.gallery_tasks.GalleryTask"]:
        """Get all the galleryTask for the given galleryGraph

        Returns:
            List[deeplabel.infer.gallery.gallery_tasks.GalleryTask]: duh, isn't that self explanatory?
        """
        return deeplabel.infer.gallery.gallery_tasks.GalleryTask.from_search_params(
            {
                "galleryId": self.gallery.gallery_id,
                "graphId": self.graph_id,
                "projectId": self.project_id,
            },
            self.client,
        )

    def update_annotated_gallery(
        self, status: AnnotatedGalleryStatus, url: Optional[str] = None
    ):
        request_data = {
            "galleryGraphId": self.gallery_graph_id,
            "annotatedGallery": {"status": status.value},
        }
        if url is not None:
            request_data["annotatedGallery"]["url"] = url  # type: ignore

        resp = self.client.put("/gallery/graphs/annotate", request_data)
        self.annotated_gallery = AnnotatedGallery(**resp.json()["data"]["annotatedGallery"])
