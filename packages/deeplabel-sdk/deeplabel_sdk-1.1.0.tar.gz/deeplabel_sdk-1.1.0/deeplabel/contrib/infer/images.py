import os
import deeplabel.client
import deeplabel
from deeplabel.infer.presign import get_upload_url, get_download_url
from PIL import Image as PILImage
from deeplabel.infer.gallery.gallery_graphs import GalleryGraph, GalleryGraphMode, GalleryGraphStatus
from deeplabel.infer.gallery import Gallery
import deeplabel.infer.gallery.images as infer_images
from urllib.parse import urlparse


class Image(infer_images.Image):

    @classmethod
    def create_from_file(
        cls,
        image_path: str,
        project_id: str,
        client: "deeplabel.client.BaseClient",
    )-> "Image":
        
        basename = os.path.basename(image_path)
        image_name = os.path.splitext(basename)[0]
        gallery_id = Gallery.create(project_id, image_name, client)
        assert os.path.exists(image_path), (
            f"Path doesn't exist {image_path} "
            f"Image upload to s3 failed for gallery {gallery_id}"
        )

        key = f"infer/gallery/{gallery_id}/images/{basename}"
        img = PILImage.open(image_path)
        width, height = img.size
        img.close()
        upload_url = get_upload_url(key,client)
        with open(image_path, "rb") as f:
            client.session.put(upload_url, f.read())
        image_url = get_download_url(key, client)

        image = super().create(image_url=image_url, gallery_id=gallery_id, project_id=project_id, name=image_name, height=height, width=width, client=client)
        return image

    @classmethod
    def create_from_url(
        cls,
        image_url: str,
        project_id: str,
        client: "deeplabel.client.BaseClient",
    )-> "Image":
        #fetch imagename from url
        parsed_url = urlparse(image_url)
        basename = os.path.basename(parsed_url.path)
        image_name = os.path.splitext(basename)[0]
        gallery_id = Gallery.create(project_id, image_name, client)
 
        image = super().create(image_url=image_url, gallery_id=gallery_id, project_id=project_id, name=image_name, height=720, width=1280, client=client)
        return image

    @property    
    def infer_status(self):
        gallery_graph = GalleryGraph.from_gallery_id(self.gallery_id, self.client)
        if len(gallery_graph) == 0:
            return GalleryGraphStatus.TBD
        gallery_graph = gallery_graph[0]
        return gallery_graph.status

    def infer(self, pipeline_id: str):
        graph = GalleryGraph.create(gallery_id= self.gallery_id, graph_id= pipeline_id, mode= GalleryGraphMode.PROD, client= self.client)
        return graph

    def get_annotations(self):
        if self.annotation_url is None or self.annotation_url == "":
            raise ValueError(f"Image {self.image_id} has no annotation_url set.")
        return self.client.session.get(self.annotation_url).json()