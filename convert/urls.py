from django.urls import path
from .views import VideoUploadView, DownloadVideoView, IndexView, upload_video_view, generate_video, upload_video, PreviewVideoView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('index-upload', upload_video_view, name='upload_video'),
    path('upload-video/', VideoUploadView.as_view(), name='upload-video'),
    path('download/<str:video_id>/', DownloadVideoView.as_view(), name='download-video'),
    path('generate-video/', generate_video, name='generate_video'),
    path('api/upload/', upload_video, name='upload_video'),
    path('preview-video/<str:video_id>/', PreviewVideoView.as_view(), name='preview-video'),
]
