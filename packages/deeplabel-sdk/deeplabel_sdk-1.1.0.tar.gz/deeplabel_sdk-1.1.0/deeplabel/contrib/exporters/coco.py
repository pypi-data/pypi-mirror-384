import json
import PIL.Image
from typing import Union, Iterable
import dataclasses
import os
from logging import getLogger
from pydantic import BaseModel
import deeplabel.label.folders
import deeplabel.label.gallery
from deeplabel.label.videos.detections import DetectionType as VideoDetectionType
from deeplabel.label.gallery.detections import ImageDetectionType
from deeplabel.label.gallery.images import Image
import deeplabel.types.bounding_box as bounding_box
import deeplabel.label.label_maps
from deeplabel.contrib.utils import image_to_name, vertices_to_bbox, replace_ids
from tqdm.contrib.concurrent import process_map  # type: ignore
import deeplabel.label.videos
import deeplabel.client
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from deeplabel.contrib.downloaders.frame_downloader import (
    GalleryImageDownloader,
    VideoAndFrameDownloader,
)
from deeplabel.exceptions import handle_deeplabel_exceptions  # type: ignore


logger = getLogger(__name__)


class BaseDoc(BaseModel):
    """Base For all docs with id key"""
    id: str


class CocoImage(BaseDoc):
    id: str
    width: int
    height: int
    file_name: str
    video_name: Optional[str]
    video_id: Optional[str]


class BaseCocoAnnotation(BaseDoc):
    image_id: str
    is_crowd: bool
    category_id: str
    area: int


class DetectionCocoAnnotation(BaseCocoAnnotation):
    id: str
    segmentation: Optional[list]
    bbox: List[Union[int, float]]


class SegmentationCocoAnnotation(BaseCocoAnnotation):
    id: str
    segmentation: list
    bbox: List[Union[int, float]]


class Category(BaseDoc):
    name: str


class CocoDataset(BaseModel):
    categories: List[Category]
    annotations: List[Union[DetectionCocoAnnotation, SegmentationCocoAnnotation]]
    images: List[CocoImage]


@dataclasses.dataclass
class CocoGalleryExporter:
    """Exporter to export 1 Gallery in coco format"""

    root_dir: str
    client: deeplabel.client.BaseClient
    categories_memo: Dict[str, Dict[str, Any]] = dataclasses.field(
        default_factory=dict
    )  # Mapping between label_id -> label

    def __post_init__(self):
        os.makedirs(self.root_dir, exist_ok=True)

    @handle_deeplabel_exceptions(lambda: ([], []))  # type: ignore
    def run(
        self,
        gallery: "deeplabel.label.gallery.Gallery",
    ):
        annotations: List[BaseCocoAnnotation] = []
        images: List[CocoImage] = []
        image_downloader = GalleryImageDownloader(gallery)
        # List of Tuple, where each tuple has Image to download and it's output path
        images_and_paths_to_download: List[Tuple[Image, str]] = []
        os.makedirs(os.path.join(self.root_dir, "images"), exist_ok=True)
        skipped = 0
        for image in gallery.images:
            if not image.detections:
                # logger.info(f"No detections for image {image.image_id}. Skipping")
                skipped+=1
                continue  # skip empty frames
            image_name = image_to_name(image)
            image_path = os.path.join(self.root_dir, "images", image_name)
            images_and_paths_to_download.append((image, image_path))
        if skipped:
            logger.warning(f"Skipping - {skipped} out of {len(gallery.images)} images in {gallery.gallery_id} because of no detections.")
        try:
            image_downloader.download_parallel(images_and_paths_to_download)
        except:
            logger.info(f"Download of some images failed in gallery - try re-running for {gallery.gallery_id}")
        
        for image in gallery.images:
            if not image.detections:
                # logger.info(f"No detections for image {image.image_id}. Skipping")
                continue  # skip empty frames
            image_name = image_to_name(image)
            image_path = os.path.join(self.root_dir, "images", image_name)
            if not os.path.exists(image_path):
                logger.error(f"Download of image - {image.image_id} has failed. Please try and rerun. ")
                continue
            img = PIL.Image.open(image_path)
            images.append(
                CocoImage( 
                    id=image.image_id,
                    height=img.height,
                    width=img.width,
                    file_name=image_name,  # type:ignore
                )
            )
            for detection in image.detections:
                if detection.type == ImageDetectionType.bounding_box and isinstance(
                    detection.bounding_box, bounding_box.BoundingBox
                ):
                    bbox = detection.bounding_box
                    w = int((bbox.xmax - bbox.xmin) * img.width)
                    h = int((bbox.ymax - bbox.ymin) * img.height)
                    annotation = DetectionCocoAnnotation(
                        id=detection.detection_id,
                        bbox=[
                            int(bbox.xmin * img.width),
                            int(bbox.ymin * img.height),
                            w,
                            h,
                        ],
                        image_id=image.image_id,
                        is_crowd=False,
                        category_id=detection.label.label_id, #type: ignore
                        area=h * w,
                    )
                elif detection.type == ImageDetectionType.polygon:
                    poly = detection.polygon.to_shapely(  # type: ignore
                        scale_x=img.width, scale_y=img.height
                    )
                    vertices=np.asarray(poly.exterior.coords).ravel().tolist()
                    bbox=vertices_to_bbox(vertices)                    
                    annotation = SegmentationCocoAnnotation(
                        id=detection.detection_id,
                        segmentation=[vertices],
                        bbox=bbox,
                        area=poly.area, #type: ignore
                        is_crowd=False,
                        category_id=detection.label.label_id, #type: ignore
                        image_id=image.image_id,
                    )
                else:
                    logger.debug(
                        f"Unsupported Detection Type: {detection.type} for image {image.image_id} for coco format.. Skipping"
                    )
                    continue
                annotations.append(annotation)
        return images, annotations


@dataclasses.dataclass
class CocoVideoExporter:
    """Exporter to export 1 video in coco format"""

    root_dir: str
    client: deeplabel.client.BaseClient
    categories_memo: Dict[str, Dict[str, Any]] = dataclasses.field(
        default_factory=dict
    )  # Mapping between label_id -> label
    write_frames: bool = False

    def __post_init__(self):
        os.makedirs(self.root_dir, exist_ok=True)

    @handle_deeplabel_exceptions(lambda: ([], []))
    def run(
        self,
        video: "deeplabel.label.videos.Video",
    ):
        annotations: List[BaseCocoAnnotation] = []
        frames: List[CocoImage] = []
        video_path = os.path.join(self.root_dir, "videos", video.video_id + ".mp4")
        frame_downloader = VideoAndFrameDownloader(video, video_path)
        for frame in video.frames:
            if not frame.detections:
                continue  # skip empty frames
            frame_path = os.path.join(self.root_dir, "images", video.video_id, frame.name)
            if self.write_frames:
                frame_path = frame_downloader.download(frame, frame_path)
                if not frame_path:
                    continue
            frames.append(
                CocoImage(
                    id=frame.frame_id,
                    url=frame.frame_url,
                    height=frame.resolution.height,
                    width=frame.resolution.width,
                    file_name=os.path.basename(frame_path),  # type:ignore
                    video_id=video.video_id,
                    video_name=video.title,
                )
            )
            for detection in frame.detections:
                if detection.type == VideoDetectionType.BOUNDING_BOX and isinstance(
                    detection.bounding_box, bounding_box.BoundingBox
                ):
                    bbox = detection.bounding_box
                    w = int((bbox.xmax - bbox.xmin) * frame.resolution.width)
                    h = int((bbox.ymax - bbox.ymin) * frame.resolution.height)
                    annotation = DetectionCocoAnnotation(
                        id=detection.detection_id,
                        bbox=[
                            int(bbox.xmin * frame.resolution.width),
                            int(bbox.ymin * frame.resolution.height),
                            w,
                            h,
                        ],
                        image_id=frame.frame_id,
                        is_crowd=False,
                        category_id=detection.label.label_id,
                        area=h * w,
                    )
                elif detection.type == VideoDetectionType.POLYGON:
                    poly = detection.polygon.to_shapely(
                        scale_x=frame.resolution.width, scale_y=frame.resolution.height
                    )
                    vertices=np.asarray(poly.exterior.coords).ravel().tolist()
                    bbox=vertices_to_bbox(vertices)
                    annotation = SegmentationCocoAnnotation(
                        id=detection.detection_id,
                        segmentation=[vertices],
                        bbox=bbox,
                        area=poly.area,
                        is_crowd=False,
                        category_id=detection.label.label_id,
                        image_id=frame.frame_id,
                    )
                else:
                    logger.debug(
                        f"Unsupported Detection Type: {detection.type} for videoId {video.video_id} for coco format.. Skipping"
                    )
                    continue
                annotations.append(annotation)

        return frames, annotations


@dataclasses.dataclass
class CocoExporter:
    root_dir: str
    client: "deeplabel.client.BaseClient"
    append: bool = True

    def __post_init__(self):
        logger.info(f"Exporting in coco format to {self.root_dir}")

    def get_existing_dataset(self, dataset_path:str) -> CocoDataset:
        if os.path.exists(dataset_path):
            with open(dataset_path, "r") as f:
                existing_dataset = json.load(f)
            existing_dataset = CocoDataset(**existing_dataset)
        else:
            existing_dataset = CocoDataset(categories=[], annotations=[], images=[])
        return existing_dataset

    def dataset_path(self, folder: deeplabel.label.folders.RootFolder, video_id):
        """If the folder is a root folder, it represents the project root. So export as Project_Videos_Dataset_xxyyzz"""
        prefix = ""
        suffix = ""
        if type(folder) is deeplabel.label.folders.RootFolder:
            prefix += "Project_"
            suffix = folder.project_id
        elif type(folder) is deeplabel.label.folders.Folder:
            prefix += "Folder_"
            suffix = folder.folder_id
        else:
            raise ValueError(f"Passed folder: {folder} is not of type Folder or RootFolder")
        if folder.type == deeplabel.label.folders.FolderType.VIDEO:
            prefix += "Videos_"
        else:
            prefix += "Gallery_"
        return prefix + suffix + f'_{video_id}' ".json"

    def export(self, folder: deeplabel.label.folders.RootFolder, write_frames:bool = False):
        os.makedirs(self.root_dir, exist_ok=True)
        categories = self.project_id2categories(folder.project_id, self.client)
        if folder.type == deeplabel.label.folders.FolderType.VIDEO:
            exporter = CocoVideoExporter(root_dir=self.root_dir, client=self.client, write_frames=write_frames)
            fav = process_map(exporter.run, folder.videos)
            fav: List[
                Tuple[List[CocoImage], List[BaseCocoAnnotation]]
            ]  # frames_and_annotations_per_video
        elif folder.type == deeplabel.label.folders.FolderType.GALLERY:
            exporter = CocoGalleryExporter(root_dir=self.root_dir, client=self.client)
            total_images = 0
            total_skipped = 0
            for gallery in folder.galleries:
                for image in gallery.images:
                    if not image.detections:
                        total_skipped+=1
                    total_images+=1
            logger.info(f'Total of {total_images} images out of which {total_skipped} images will be skipped due to no detections')
            fav = process_map(exporter.run, folder.galleries)
        else:
            raise ValueError(f"Folder {folder.folder_id} has not folder valid type.")

        # Serialize the images/annotations from per_video lists to a single list
        for imgs, anns in fav:
            images:List[CocoImage] = []
            annotations:List[BaseCocoAnnotation] = []
            images.extend(imgs)
            annotations.extend(anns)
            dataset = CocoDataset(
                categories=categories, annotations=annotations, images=images
            )
            if not len(images):
                continue
            video_id = images[0].video_id
            # Either only keep the new images or append to existing images, annotations and categories
            dataset_path = os.path.join(self.root_dir, self.dataset_path(folder, video_id))
            if self.append:
                existing_dataset = self.get_existing_dataset(dataset_path)
                dataset = CocoDataset(
                    categories=self.merge_docs_by_id(
                        existing_dataset.categories, dataset.categories
                    ),
                    annotations=self.merge_docs_by_id(
                        existing_dataset.annotations, dataset.annotations
                    ),
                    images=self.merge_docs_by_id(existing_dataset.images, dataset.images),
                )

            with open(dataset_path, "w") as f:
                # exclude unset will skip the video_id and video_name in images if unset
                json.dump(dataset.dict(exclude_unset=True), f, indent=4)
            
            replace_ids(dataset_path)

    @staticmethod
    def project_id2categories(project_id: str, client: "deeplabel.client.BaseClient"):
        LabelMap = deeplabel.label.label_maps.LabelMap
        labelmaps: List[LabelMap] = LabelMap.from_search_params(
            {"projectId": project_id, "limit": "-1"}, client
        )
        
        categories = [
             Category(id= labelmap.label_id, name=labelmap.label.name)
            for labelmap in labelmaps
        ]
        return categories

    @staticmethod
    def merge_docs_by_id(old_many: Iterable[BaseDoc], new_many: Iterable[BaseDoc]):
        """Given 2 set of Docs of same type, merge them, skipping old doc if it exists in new_many

        Args:
            old_many (List[BaseDoc]): List of existing docs
            new_many (List[BaseDoc]): List of new docs

        Returns:
            List[BaseDoc]: List of merged Docs
        """
        new_memo = {new_doc.id: new_doc for new_doc in new_many}
        # return existing document if it exists, else return from new doc
        to_keep = [doc for doc in old_many if doc.id not in new_memo]
        return [*new_many, *to_keep]
