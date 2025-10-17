import os
import wget
from typing import Any, Dict, List, Optional
from pydantic import Field
import deeplabel.client
import deeplabel
from deeplabel.exceptions import InvalidIdError
import deeplabel.infer.gallery.gallery_tasks
from deeplabel.basemodel import DeeplabelBase, MixinConfig


class ImageResolution(MixinConfig):
    height: Optional[int]
    width: Optional[int]


class Image(DeeplabelBase):
    gallery_id: str
    project_id: str
    image_id: str
    image_url: str
    name: str
    annotation_url: Optional[str]
    parent_folder_id: Optional[str]
    resolution: ImageResolution = Field(default_factory=ImageResolution)  # type: ignore
    
    def download_annotations(self, folder_or_file_path:str):
        if self.annotation_url is None or self.annotation_url == "":
            raise ValueError(f"Image {self.image_id} has no annotation_url set.")
        wget.download(self.annotation_url, out=folder_or_file_path) # type: ignore

    @classmethod
    def create(
        cls,
        image_url: str,
        gallery_id: str,
        project_id: str,
        name: str,
        height: int,
        width: int,
        client: "deeplabel.client.BaseClient",
    )-> "Image":
        json = dict(
            batch=True,
            data = [
                dict(
                    projectId=project_id,
                    galleryId=gallery_id,
                    imageUrl=image_url,
                    name=name,
                    resolution=dict(
                        height=height,
                        width=width
                    )
                )
            ]
        )
            
        resp = client.post('/images', json=json)
        return cls(**resp.json()['data'][0], client=client)

    @classmethod
    def from_search_params(
        cls, params: Dict[str, Any], client: "deeplabel.client.BaseClient"
    ) -> List["Image"]:
        images = []
        if 'limit' in params and (params['limit'] == -1 or params['limit'] == '-1'):
            page = 1
            limit = 500
            while True:
                params['limit'] = limit
                params['page'] = page
                resp = client.get("/images", params=params)
                data = resp.json()["data"]["images"]
                if not len(data):
                    break
                images.extend(data)
                page += 1
        else:
            resp = client.get("/images", params=params)
            images = resp.json()["data"]["images"]

        images = [cls(**image, client=client) for image in images]
        return images  # type: ignore

    @classmethod
    def from_image_id(
        cls, image_id: str, client: "deeplabel.client.BaseClient"
    ) -> "Image":
        image = cls.from_search_params({"imageId": image_id}, client=client)
        if not len(image):
            raise InvalidIdError(f"Failed to fetch image with imageId: {image_id}")
        return image[0]

    @classmethod
    def from_gallery_and_project_id(
        cls, gallery_id: str, project_id: str, client: "deeplabel.client.BaseClient"
    ) -> List["Image"]:
        return cls.from_search_params(
            {"galleryId": gallery_id, "projectId": project_id, "limit": "-1"},
            client=client,
        )
