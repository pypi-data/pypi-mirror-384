import cv2
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
from deeplabel.contrib.utils import image_to_name, pascal_voc_color_map
from tqdm.contrib.concurrent import process_map
import deeplabel.label.videos
import deeplabel.client
import PIL.Image
from typing import List, Dict, Any, Tuple
import numpy as np
from deeplabel.contrib.downloaders.frame_downloader import (
    GalleryImageDownloader,
    VideoAndFrameDownloader,
)
import pascal_voc_writer
from deeplabel.exceptions import handle_deeplabel_exceptions


logger = getLogger(__name__)


@dataclasses.dataclass
class GalleryExporter:

    root_dir: str
    client: deeplabel.client.BaseClient
    label_to_int: Dict[str, int]
    categories_memo: Dict[str, Dict[str, Any]] = dataclasses.field(
        default_factory=dict
    )  # Mapping between label_id -> label
    export_frames: bool = False

    def __post_init__(self):
        jpeg_images_dir = os.path.join(self.root_dir, 'JPEGImages')
        os.makedirs(self.root_dir, exist_ok=True)
        if self.export_frames:
            os.makedirs(jpeg_images_dir, exist_ok=True)

    @handle_deeplabel_exceptions(lambda: None)
    def run(
        self,
        gallery: "deeplabel.label.gallery.Gallery",
    ):
        image_downloader = GalleryImageDownloader(gallery)
        # Since each image is independent, it's faster to download them in parallel
        # List of Tuple, where each tuple has Image to download and it's output path
        images_and_paths_to_download: List[Tuple[Image, str]] = []
        for image in gallery.images:
            if not image.detections:
                logger.info(f"No detections for image {image.image_id}. Skipping")
                continue  # skip empty frames
            image_name = image_to_name(image)
            image_path = os.path.join(self.root_dir, "JPEGImages", image_name)
            images_and_paths_to_download.append((image, image_path))
            segmented = np.any(
                [1 for d in image.detections if d.type == ImageDetectionType.polygon]
            )
            if segmented:
                mask = np.zeros(
                    (image.resolution.height, image.resolution.width), dtype="uint8"
                )
            pascal_voc_image_annotation = pascal_voc_writer.Writer(
                image_path,
                image.resolution.width,
                image.resolution.height,
                gallery.title,
                segmented=int(segmented),
                database=image.image_url,
            )
            for detection in image.detections:
                if detection.type == ImageDetectionType.bounding_box and isinstance(
                    detection.bounding_box, bounding_box.BoundingBox
                ):
                    pascal_voc_image_annotation.addObject(
                        detection.label.name,
                        int(detection.bounding_box.xmin * image.resolution.width),
                        int(detection.bounding_box.ymin * image.resolution.height),
                        int(detection.bounding_box.xmax * image.resolution.width),
                        int(detection.bounding_box.ymax * image.resolution.height),
                    )
                elif detection.type == ImageDetectionType.polygon:
                    poly = detection.polygon.to_shapely(
                        scale_x=image.resolution.width, scale_y=image.resolution.height
                    )
                    pts = [np.asarray(poly.exterior.coords).astype(int)]
                    mask = cv2.fillPoly(
                        mask, pts, [self.label_to_int[detection.label.label_id]]
                    )
                    mask = cv2.polylines(
                        mask, pts, isClosed=True, color=[255], thickness=5
                    )
                else:
                    pascal_voc_image_annotation.addObject(  # type: ignore
                        detection.label.name, 0, 0, 1, 1
                    )
            os.makedirs(os.path.join(self.root_dir, "Annotations"), exist_ok=True)
            os.makedirs(os.path.join(self.root_dir, "SegmentationClass"), exist_ok=True)
            # save annotation
            pascal_voc_image_annotation.save(
                os.path.join(
                    self.root_dir,
                    "Annotations",
                    os.path.splitext(image_name)[0] + ".xml",
                )
            )
            # save segmentation mask if any
            if segmented:
                segmentation = PIL.Image.fromarray(mask)
                segmentation.putpalette(pascal_voc_color_map())
                segmentation.save(
                    os.path.join(
                        self.root_dir,
                        "SegmentationClass",
                        os.path.splitext(image_name)[0] + ".png",
                    )
                )

        if self.export_frames:
            image_downloader.download_parallel(images_and_paths_to_download)


@dataclasses.dataclass
class VideoExporter:
    """Exporter to export 1 video in pascalVoc format"""

    root_dir: str
    client: deeplabel.client.BaseClient
    label_to_int: Dict[str, int]
    categories_memo: Dict[str, Dict[str, Any]] = dataclasses.field(
        default_factory=dict
    )  # Mapping between label_id -> label
    write_frames: bool = False

    def __post_init__(self):
        os.makedirs(self.root_dir, exist_ok=True)

    @handle_deeplabel_exceptions(lambda: None)
    def run(
        self,
        video: "deeplabel.label.videos.Video",
    ):
        video_path = os.path.join(self.root_dir, "videos", video.video_id + ".mp4")
        frame_downloader = VideoAndFrameDownloader(video, video_path)
        for frame in video.frames:
            if not frame.detections:
                continue  # skip empty frames
            frame_path = os.path.join(
                self.root_dir, "JPEGImages", video.video_id, f"{frame.number}.jpg"
            )
            if self.write_frames:
                frame_downloader.download(frame, frame_path)
            height = int(frame_downloader.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            width = int(frame_downloader.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            segmented = np.any(
                [1 for d in frame.detections if d.type == VideoDetectionType.POLYGON]
            )
            if segmented:
                mask = np.zeros((height, width), dtype="uint8")
            pascal_voc_frame_annotation = pascal_voc_writer.Writer(
                frame_path,
                width,
                height,
                database=video.video_id,
                segmented=int(segmented),
            )
            for detection in frame.detections:
                if detection.type == VideoDetectionType.BOUNDING_BOX and isinstance(
                    detection.bounding_box, bounding_box.BoundingBox
                ):
                    bbox = detection.bounding_box
                    pascal_voc_frame_annotation.addObject(
                        detection.label.name,
                        int(detection.bounding_box.xmin * width),
                        int(detection.bounding_box.ymin * height),
                        int(detection.bounding_box.xmax * width),
                        int(detection.bounding_box.ymax * height),
                    )
                elif detection.type == VideoDetectionType.POLYGON:
                    poly = detection.polygon.to_shapely(scale_x=width, scale_y=height)
                    pts = [np.asarray(poly.exterior.coords).astype(int)]
                    mask = cv2.fillPoly(
                        mask, pts, [self.label_to_int[detection.label.label_id]]
                    )
                    mask = cv2.polylines(
                        mask, pts, isClosed=True, color=[255], thickness=5
                    )
                else:
                    pascal_voc_frame_annotation.addObject(
                        detection.label.name, 0, 0, 1, 1
                    )
                    logger.debug(
                        f"Unsupported Detection Type: {detection.type} for video {video.video_id} for pascalVoc format.. Skipping"
                    )
                    continue

            annotations_root = os.path.join(
                self.root_dir, "Annotations", video.video_id
            )
            segmentation_root = os.path.join(
                self.root_dir, "SegmentationClass", video.video_id
            )
            os.makedirs(annotations_root, exist_ok=True)
            os.makedirs(segmentation_root, exist_ok=True)
            # save annotation
            pascal_voc_frame_annotation.save(
                os.path.join(annotations_root, frame.frame_id + ".xml")
            )
            # save segmentation mask if any
            if segmented:
                segmentation = PIL.Image.fromarray(mask)
                segmentation.putpalette(pascal_voc_color_map())
                segmentation.save(
                    os.path.join(segmentation_root, frame.frame_id + ".png")
                )


@dataclasses.dataclass
class PascalVocExporter:
    root_dir: str
    client: "deeplabel.client.BaseClient"

    def export(
        self, folder: deeplabel.label.folders.RootFolder, write_frames: bool = False
    ):
        # map label_id -> 1,2,3,...
        label_to_int = self.project_label_ints(folder.project_id, self.client)
        if folder.type == deeplabel.label.folders.FolderType.VIDEO:
            exporter = VideoExporter(
                root_dir=self.root_dir,
                client=self.client,
                label_to_int=label_to_int,
                write_frames=write_frames,
            )
            process_map(exporter.run, folder.videos)
        elif folder.type == deeplabel.label.folders.FolderType.GALLERY:
            exporter = GalleryExporter(
                root_dir=self.root_dir, client=self.client, label_to_int=label_to_int, export_frames=write_frames,
            )
            process_map(exporter.run, folder.galleries)

    @staticmethod
    def project_label_ints(project_id, client: "deeplabel.client.BaseClient"):
        """
        Map label_id -> 1,2,3,...
        """
        LabelMap = deeplabel.label.label_maps.LabelMap
        labelmaps: List[LabelMap] = LabelMap.from_search_params(
            {"projectId": project_id, "limit": "-1"}, client
        )
        labelmaps = sorted(labelmaps, key=lambda labelmap: labelmap.label_id)
        return {labelmap.label_id: i for i, labelmap in enumerate(labelmaps)}
