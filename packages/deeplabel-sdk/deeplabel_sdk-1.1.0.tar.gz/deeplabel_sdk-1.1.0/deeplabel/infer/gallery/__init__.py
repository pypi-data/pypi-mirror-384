"""
Module to get videos data
"""
import os
import uuid
from typing import Any, Dict, List, Optional
import deeplabel.client
from PIL import Image as PILImage
import deeplabel
from deeplabel.exceptions import InvalidIdError
import deeplabel.infer.gallery.gallery_tasks
import deeplabel.infer.gallery.images
from deeplabel.basemodel import DeeplabelBase
from deeplabel.infer.presign import get_upload_url, get_download_url
from logging import getLogger

logger = getLogger(__file__)


class Gallery(DeeplabelBase):
    gallery_id: str
    project_id: str
    title: str
    parent_folder_id: Optional[str]

    @classmethod
    def create(
        cls,
        project_id: str,
        title: str,
        client: "deeplabel.client.BaseClient",
    )-> "Gallery":
        json = {
                "projectId": project_id,
                "title": title,
            }
        resp = client.post('/gallery', json=json)
        return resp.json()['data']['galleryId']

    @classmethod
    def from_search_params(
        cls, params: Dict[str, Any], client: "deeplabel.client.BaseClient"
    ) -> List["Gallery"]:
        galleries = []
        if 'limit' in params and (params['limit'] == -1 or params['limit'] == '-1'):
            page = 1
            limit = 500
            while True:
                params['limit'] = limit
                params['page'] = page
                resp = client.get("/gallery", params=params)
                data = resp.json()["data"]["gallery"]
                if not len(data):
                    break
                galleries.extend(data)
                page += 1
        else:
            resp = client.get("/gallery", params=params)
            galleries = resp.json()["data"]["gallery"]

        galleries = [cls(**gallery, client=client) for gallery in galleries]
        return galleries  # type: ignore

    @classmethod
    def from_gallery_id(
        cls, gallery_id: str, client: "deeplabel.client.BaseClient"
    ) -> "Gallery":
        gallery = cls.from_search_params({"galleryId": gallery_id}, client=client)
        if not len(gallery):
            raise InvalidIdError(f"Failed to fetch video with videoId: {gallery_id}")
        return gallery[0]

    @classmethod
    def from_folder_id(
        cls, folder_id: str, client: "deeplabel.client.BaseClient"
    ) -> List["Gallery"]:
        return cls.from_search_params({"parentFolderId": folder_id}, client)

    @property
    def images(self) -> List["deeplabel.infer.gallery.images.Image"]:
        return deeplabel.infer.gallery.images.Image.from_gallery_and_project_id(
            self.gallery_id, self.project_id, self.client
        )

    @property
    def gallery_tasks(self):
        return deeplabel.infer.gallery.gallery_tasks.GalleryTask.from_gallery_id(
            self.gallery_id, self.client
        )

    def insert_processed_image(
        self, image_path: str
    ) -> "deeplabel.infer.gallery.images.Image":
        """Insert analytics image to the gallery for easy review after processing
        Make sure you don't call infer on the galleries after using this.
        """
        assert os.path.exists(image_path), (
            f"Path doesn't exist {image_path} "
            f"Image upload to s3 failed for gallery {self.gallery_id}"
        )
        basename = os.path.basename(image_path)
        image_name = os.path.splitext(basename)[0]
        key = f"inference/{self.gallery_id}/{uuid.uuid4()}/{basename}"

        img = PILImage.open(image_path)
        width, height = img.size
        img.close()
        upload_url = get_upload_url(key, self.client)
        with open(image_path, "rb") as f:
            self.client.session.put(upload_url, f.read())
        image_url = get_download_url(key, self.client)
        logger.debug(f"Done uploading the image to {key}")
        return deeplabel.infer.gallery.images.Image.create(
            image_url,
            self.gallery_id,
            self.project_id,
            image_name,
            height,
            width,
            self.client,
        )
