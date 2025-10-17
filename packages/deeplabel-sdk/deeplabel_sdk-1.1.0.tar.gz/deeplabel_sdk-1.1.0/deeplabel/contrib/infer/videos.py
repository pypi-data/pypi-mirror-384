from deeplabel.infer.videos import Video as VideoInfer  
from deeplabel.infer.videos.video_graphs import VideoGraph, VideoGraphStatus, VideoGraphMode
from deeplabel.infer.presign import get_upload_url, get_download_url
import os
import wget


class Video(VideoInfer):
    @classmethod
    def create_from_file(
        cls,
        video_path: str,
        project_id: str,
        client: "deeplabel.client.BaseClient",
    )-> "Video":
        
        basename = os.path.basename(video_path)
        assert os.path.exists(video_path), (
            f"Path doesn't exist {video_path} "
            f"Video upload to s3 failed"
        )

        key = f"infer/video/{basename}"
        upload_url = get_upload_url(key,client)
        with open(video_path, "rb") as f:
            client.session.put(upload_url, f.read())
        video_url = get_download_url(key, client)

        video_id = super().create(input_url=video_url, project_id=project_id, client=client)

        return video_id
    
    @classmethod
    def create_from_url(
        cls,
        video_url: str,
        project_id: str,
        client: "deeplabel.client.BaseClient",
    )-> "Video":
        video_id = super().create(input_url=video_url, project_id=project_id, client=client)

        return video_id


    @property    
    def infer_status(self):
        video_graphs = VideoGraph.from_video_id(self.video_id, self.client)
        if len(video_graphs) == 0:
            return VideoGraphStatus.TBD
        video_graph = video_graphs[0]
        return video_graph.status

    def infer(self, pipeline_id: str):
        graph = VideoGraph.create(video_id= self.video_id, graph_id= pipeline_id, mode= VideoGraphMode.PROD, client= self.client)
        return graph

    def download_video(self, output_path: str):
        if self.video_url is None:
            raise ValueError("Video url is None")
        wget.download(self.video_url, out=output_path)

