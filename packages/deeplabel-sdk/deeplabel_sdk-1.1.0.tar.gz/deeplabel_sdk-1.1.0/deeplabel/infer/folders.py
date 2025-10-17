from typing import Any, Dict, List, Optional
from enum import Enum
from deeplabel.exceptions import InvalidIdError
from deeplabel.basemodel import DeeplabelBase
import deeplabel.label.videos
import deeplabel.label.gallery
import deeplabel.label.folders
import deeplabel.client
import deeplabel


class FolderType(Enum):
    VIDEO = "VIDEO"
    GALLERY = "GALLERY"


class RootFolder(DeeplabelBase):
    type: Optional[FolderType]
    folder_id: Optional[str]
    project_id: str

    @property
    def folders(self):
        search_params = {"projectId": self.project_id}
        if self.folder_id is not None:
            search_params["parentFolderId"] = self.folder_id
        if self.type is not None:
            search_params["type"] = self.type.value
        return deeplabel.label.folders.Folder.from_search_params(
            search_params, self.client
        )

    @property
    def videos(self) -> List["deeplabel.label.videos.Video"]:
        search_params = {
            "projectId": self.project_id,
            "limit": "-1",
        }
        if self.folder_id is not None:
            search_params["parentFolderId"] = self.folder_id
        return deeplabel.label.videos.Video.from_search_params(
            search_params, client=self.client,
        )

    @property
    def galleries(self) -> List["deeplabel.label.gallery.Gallery"]:
        search_params = {
            "projectId": self.project_id,
            "limit": "-1",
        }
        if self.folder_id is not None:
            search_params["parentFolderId"] = self.folder_id
        return deeplabel.label.gallery.Gallery.from_search_params(
            search_params, client=self.client,
        )


class Folder(RootFolder):
    description: str
    name: str
    parent_folder_id: Optional[str]
    ancestor_folder_ids: List[str]

    @classmethod
    def create(
        cls,
        name: str,
        project_id: str,
        client: "deeplabel.client.BaseClient",
        type: FolderType = FolderType.VIDEO,
        description: str = "",
        parent_folder_id: str = "project",
    ):
        request_data = {
            "projectId": project_id,
            "name": name,
            "type": type.value,
            "parentFolderId": parent_folder_id,
            "description": description,
            "restriction": "false"
        }
        resp = client.post("/folders", request_data)
        return cls(**resp.json()["data"])

    @classmethod
    def from_search_params(
        cls, params: Dict[str, Any], client: "deeplabel.client.BaseClient"
    ) -> List["Folder"]:
        resp = client.get("/folders", params)
        folders = resp.json()["data"]["folders"]
        folders = [cls(**folder, client=client) for folder in folders]
        return folders  # type: ignore

    @classmethod
    def from_project_id(
        cls, project_id: str, client: "deeplabel.client.BaseClient"
    ) -> List["Folder"]:
        folders = cls.from_search_params({"projectId": project_id}, client)
        return folders

    @classmethod
    def from_folder_id(
        cls, folder_id: str, client: "deeplabel.client.BaseClient"
    ) -> "Folder":
        folders = cls.from_search_params({"folderId": folder_id}, client)
        if not folders:
            raise InvalidIdError(f"No Folder found with folderId: {folder_id}")
        return folders[0]

