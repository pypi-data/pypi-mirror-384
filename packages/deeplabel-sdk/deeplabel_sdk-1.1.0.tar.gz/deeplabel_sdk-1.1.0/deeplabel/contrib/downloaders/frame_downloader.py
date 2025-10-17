import os
from urllib.error import HTTPError
import cv2
from typing import List, Tuple
from logging import getLogger
import logging
import wget  # type: ignore
import dataclasses
from dataclasses import field
from concurrent.futures import ThreadPoolExecutor
from deeplabel.label.videos import Video
from deeplabel.label.gallery import Gallery
from deeplabel.label.videos.frames import Frame
from deeplabel.label.gallery.images import Image
from tqdm.contrib.concurrent import process_map #type: ignore
from deeplabel.exceptions import DownloadFailed
from urllib.parse import quote
from urllib.parse import urlparse, urlunparse
import requests
from requests.adapters import HTTPAdapter, Retry
from urllib3.exceptions import ProtocolError
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = getLogger(__name__)



@dataclasses.dataclass
class VideoAndFrameDownloader:
    """Download frame and extract the required frame"""

    video: Video
    video_path: str
    cap: cv2.VideoCapture = field(init=False)  # cv2.cap object

    def __post_init__(self):
        video: Video = self.video
        os.makedirs(os.path.dirname(self.video_path), exist_ok=True)
        if os.path.exists(self.video_path):
            logger.debug(f"Video {video.video_id} already exists... Skipping Download")
        else:
            try:
                # wget.download(video.video_url, self.video_path)  # type: ignore
                # downloading with requests is more robust, wget gives error when urls contain spaces and special characters
                response = requests.get(video.video_url, stream=True)
                with open(self.video_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            except HTTPError as e:
                logger.debug(
                    f"Video Download Failed for videoId {video.video_id}, url {video.video_url}"
                )
                DownloadFailed(f"Download failed for {video.video_id}.. {e}")
        if not os.path.exists(self.video_path):
            raise DownloadFailed(
                f"Video Download failed for videoId: {video.video_id} from "
                f"url: {video.video_url}"
            )
        self.cap = cv2.VideoCapture(self.video_path)

    def download(self, frame: Frame, frame_path: str):
        os.makedirs(os.path.dirname(frame_path), exist_ok=True)
        if frame.video_id != self.video.video_id:
            raise ValueError(
                f"passed frame {frame.frame_id} is not for video {self.video.video_id}"
            )
        # due to round off, we might end up accessing a frame beyond the number of frames, hence we skip those.
        if frame.number > self.video.duration * self.video.video_fps:
            logger.info(f'Trying to access invalid frame {frame.frame_id}, (number: {frame.number}) skipping')
            return None
        if os.path.exists(frame_path):
            logger.debug(f"frame {frame.frame_id} already exists. Skipping")
        else:
            try:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame.number)  # type: ignore
                success, img = self.cap.read()  # type: ignore
                if not success:
                    logger.warning(f'OpenCV unable to read {frame.frame_id}, (number: {frame.number}) skipping')
                    return None
                cv2.imwrite(frame_path, img)  # type: ignore
            except:
                raise Exception(f'Failed to read frame { frame.number} using openvc for videoId {self.video.video_id}')
        return frame_path


@dataclasses.dataclass
class GalleryImageDownloader:
    """Given a gallery and its images, download each image to the given location."""

    gallery: 'Gallery'

    def __post_init__(self):
        """Create a single session per instance with retry logic."""
        self.session = requests.Session()
        retries = Retry(
            total=5,
            connect=5,
            read=5,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def download(self, image: 'Image', image_path: str) -> str:
        """Download image robustly with retries and connection error handling"""
        if os.path.exists(image_path):
            logger.info(f"Image {image.image_id} already exists. Skipping download.")
            return image_path

        success = False
        try:
            with self.session.get(image.image_url, stream=True, timeout=(10, 60)) as r:
                r.raise_for_status()
                with open(image_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        if chunk:
                            f.write(chunk)
            success = True  # mark success only if no exception occurred

        except (requests.exceptions.ConnectionError, ProtocolError) as e:
            logger.warning(f"Temporary connection error downloading {image.image_id}: {e}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"HTTP error downloading {image.image_id}: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error downloading {image.image_id}: {e}")

        # Validate final file
        if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
            raise DownloadFailed(f"Failed to download image {image.image_id} at {image_path}")

        # Log only if the final result is successful
        # if success:
        #     logger.info(f"Downloaded image {image.image_id} successfully to {image_path}")

        return image_path

    def download_parallel(self, images_and_paths: List[Tuple['Image', str]]) -> List[str]:
        """Download multiple images in parallel using process_map."""
        try:
            # images, paths = zip(*images_and_paths)
            def helper(input_tuple):
                image,path = input_tuple
                return self.download(image,path)

            with ThreadPoolExecutor(min(10, os.cpu_count())) as exe:
                exe.map(helper,images_and_paths)

        except Exception as e:
            logger.exception(f"Download parallel function has error: {e}")
            raise