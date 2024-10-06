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
import os
import logging
from django.http import JsonResponse
from django.shortcuts import render

logging.basicConfig(level=logging.DEBUG)
# Directory to store uploaded files
UPLOAD_DIRECTORY = "uploads"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

from django.views.generic import TemplateView

class IndexView(TemplateView):
    template_name = 'index.html'

class VideoUploadView(APIView):
    def post(self, request):
        serializer = VideoUploadSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            # Save video file
            video_id = str(uuid.uuid4())
            video_name = f"{video_id}-{data['file'].name}"
            video_location = os.path.join(UPLOAD_DIRECTORY, video_name)
            with open(video_location, "wb+") as video_file:
                video_file.write(data['file'].read())
            
            # Save other files
            transcript_location = os.path.join(UPLOAD_DIRECTORY, data['transcript'].name)
            with open(transcript_location, "wb+") as transcript_file:
                transcript_file.write(data['transcript'].read())

            translation_location = os.path.join(UPLOAD_DIRECTORY, data['translation'].name)
            with open(translation_location, "wb+") as translation_file:
                translation_file.write(data['translation'].read())

            font_location = os.path.join(UPLOAD_DIRECTORY, data['font'].name)
            with open(font_location, "wb+") as font_file:
                font_file.write(data['font'].read())

            # Structure the response with metadata and file locations
            video_info = {
                "video_location": video_location,
                "transcript_location": transcript_location,
                "translation_location": translation_location,
                "font_location": font_location,
                "font_size": data['font_size'],
                "font_color": data['font_color'],
                "box_color": data['box_color'],
                "box_width": data['box_width'],
                "box_height": data['box_height'],
                "video_name": video_name,
                "video_id": video_id,
                "eleven_labs": data['eleven_labs'],
                "voice_id": data['voice_id']
            }

            process_video(video_info)

            return Response({"message": "Files uploaded and processed successfully", "video_info": video_info}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DownloadVideoView(APIView):
    def get(self, request, video_id):
        try: 
            video_path = os.path.join(os.getcwd(), "static", "final", f"{video_id}.mp4")
            print("", video_path)
            with open(video_path, 'rb') as video_file:
                response = HttpResponse(video_file.read(), content_type='video/mp4')
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(video_path)}"'
                return response
        except Exception as e:
            return Response({"detail": f"Error while trying to download file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def upload_video_view(request):
    return render(request, 'index_upload.html')


def generate_video(request):

    return JsonResponse({'message': 'Video generated successfully!', 'video_path': generate_video_test()}, status=200)

    

