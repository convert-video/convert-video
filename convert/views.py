# converterapp/views.py
from django.http import JsonResponse, HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import VideoUploadSerializer
import os
import uuid
from .converter import process_video
from .converttest import generate_video_test
from django.http import JsonResponse
from django.http import StreamingHttpResponse
import logging
from pathlib import Path
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from rest_framework.decorators import api_view
from moviepy.editor import VideoFileClip
from django.shortcuts import render

from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.utils import timezone
from mainapps.payment.models import UserSubscription
from django.db.models import F
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from django.http import JsonResponse
from django.views import View


logging.basicConfig(level=logging.DEBUG)
# Directory to store uploaded files
UPLOAD_DIRECTORY = "uploads"
TMP_FOLDER = "tmp"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(TMP_FOLDER, exist_ok=True)

from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = "index.html"


class IndexView(View):
    def get(self, request, *args, **kwargs):
        data = {'status': 'success', 'message': "It's working"}
        return JsonResponse(data, status=200)

class VideoUploadView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = VideoUploadSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data

            # Save video file
            video_id = str(uuid.uuid4())
            video_name = f"{video_id}-{data['file'].name}"
            video_location = os.path.join(UPLOAD_DIRECTORY, video_name)
            with open(video_location, "wb+") as video_file:
                video_file.write(data["file"].read())

            # Save other files
            transcript_location = os.path.join(
                UPLOAD_DIRECTORY, data["transcript"].name
            )
            with open(transcript_location, "wb+") as transcript_file:
                transcript_file.write(data["transcript"].read())

            translation_location = os.path.join(
                UPLOAD_DIRECTORY, data["translation"].name
            )
            with open(translation_location, "wb+") as translation_file:
                translation_file.write(data["translation"].read())

            font_location = os.path.join(UPLOAD_DIRECTORY, data["font"].name)
            with open(font_location, "wb+") as font_file:
                font_file.write(data["font"].read())

            # Structure the response with metadata and file locations
            video_info = {
                "video_location": video_location,
                "transcript_location": transcript_location,
                "translation_location": translation_location,
                "font_location": font_location,
                "font_size": data["font_size"],
                "font_color": data["font_color"],
                "box_color": data["box_color"],
                "box_width": data["box_width"],
                "box_height": data["box_height"],
                "video_name": video_name,
                "video_id": video_id,
                "eleven_labs": data["eleven_labs"],
                "voice_id": data["voice_id"],
            }

            process_video(video_info)

            # Call the function
            delete_all_files(UPLOAD_DIRECTORY)
            delete_all_files(TMP_FOLDER)

            return Response({"message": "Files uploaded and processed successfully", "video_info": video_info}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


User = get_user_model()


class DownloadVideoView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, video_id):
        self.validate_before_download(request)
        try:
            video_path = os.path.join(os.getcwd(), "static", "final", f"{video_id}.mp4")

            video_path = os.path.join(settings.MEDIA_ROOT, "final", f"{video_id}.mp4")
            # video_path = Path(os.path.join(settings.MEDIA_ROOT, 'final', f"{video_id}.mp4"))
            print("", video_path)
            with open(video_path, "rb") as video_file:
                response = HttpResponse(video_file.read(), content_type="video/mp4")
                response["Content-Disposition"] = (
                    f'attachment; filename="{os.path.basename(video_path)}"'
                )
                return response
        except Exception as e:
            return Response(
                {"detail": f"Error while trying to download file: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def validate_before_download(self, request):
        
        try:
            user= request.user
    
            logging.debug(f"[LOGGING DATA]: {user}")
            user_id = user.id
            subscriptions = self.get_expired_completed_subscriptions(user_id)
            logging.debug(f"[LOGGING DATA]: {subscriptions}")
            
            if subscriptions.count() == 0:
                raise ValidationError(
                    {"error": "Please purchase more or check your download limit."}
                )

            for subscription in subscriptions:
                subscription.amount_used_usage += 1
                subscription.save()
                break

            return user_id
        except AuthenticationFailed:
            raise ValidationError({"error": "Invalid or expired token"})

    def get_expired_completed_subscriptions(self, user_id):
        current_time = timezone.now()

        subscriptions = UserSubscription.objects.filter(
            expiration_at__gt=current_time,  # expiration_at less than amount_allowed_usage
            amount_used_usage__lt=F(
                "amount_allowed_usage"
            ),  # amount_used_usage less than amount_allowed_usage
            status="COMPLETED",  # status COMPLETED
            user_id=user_id,
        ).order_by("-created_at")

        return subscriptions
    


def upload_video_view(request):
    return render(request, "index_upload.html")


def generate_video(request):

    return JsonResponse(
        {
            "message": "Video generated successfully!",
            "video_path": generate_video_test(),
        },
        status=200,
    )


@api_view(["POST"])
def upload_video(request):
    if request.method == "POST":
        video_file = request.FILES.get("video")

        if not video_file:
            return Response(
                {"error": "No video file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Lưu video vào thư mục tạm thời
        fs = FileSystemStorage()
        filename = fs.save(video_file.name, video_file)
        video_path = os.path.join(settings.MEDIA_ROOT, filename)

        # Ghi video vào thư mục final với video_id
        video_info = {
            "video_id": filename.split(".")[0]
        }  # Giả sử video_id là tên file mà không có đuôi
        output_file = Path(
            os.path.join(settings.MEDIA_ROOT, "final", f"{video_info['video_id']}.mp4")
        )

        # Tạo thư mục nếu nó không tồn tại
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Xử lý video với MoviePy
        try:
            # Tải video để xử lý
            final_video = VideoFileClip(video_path)
            final_video.write_videofile(
                output_file.as_posix(), codec="libx264", audio_codec="aac"
            )
            logging.info(f"Generated output video: {output_file}")
            return Response(
                {
                    "message": "Video uploaded and processed successfully!",
                    "video_path": output_file.as_posix(),
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logging.error(f"Có lỗi xảy ra khi ghi video: {e}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return Response(
        {"error": "Invalid request method"}, status=status.HTTP_400_BAD_REQUEST
    )


class PreviewVideoView(APIView):
    def get(self, request, video_id):
        try:
            video_path = os.path.join(os.getcwd(), "static", "final", f"{video_id}.mp4")
            # Alternatively, if using MEDIA_ROOT:
            # video_path = Path(os.path.join(settings.MEDIA_ROOT, 'final', f"{video_id}.mp4"))

            if not os.path.exists(video_path):
                return Response(
                    {"detail": "Video not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Use StreamingHttpResponse to stream the video
            response = StreamingHttpResponse(
                open(video_path, "rb"), content_type="video/mp4"
            )
            response["Content-Length"] = os.path.getsize(
                video_path
            )  # Optional: set content length for better behavior
            return response
        except Exception as e:
            return Response(
                {"detail": f"Error while trying to preview video: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

def delete_all_files(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            

