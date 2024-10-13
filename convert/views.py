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
from django.http import StreamingHttpResponse
import os
import logging
from pathlib import Path
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from rest_framework.decorators import api_view
from moviepy.editor import VideoFileClip

from django.http import JsonResponse
from django.views import View

logging.basicConfig(level=logging.DEBUG)
# Directory to store uploaded files
UPLOAD_DIRECTORY = "uploads"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

class IndexView(View):
    def get(self, request, *args, **kwargs):
        data = {'status': 'success', 'message': "It's working"}
        return JsonResponse(data, status=200)

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
            # video_path = Path(os.path.join(settings.MEDIA_ROOT, 'final', f"{video_id}.mp4"))
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

    
@api_view(['POST'])
def upload_video(request):
    if request.method == 'POST':
        video_file = request.FILES.get('video')

        if not video_file:
            return Response({'error': 'No video file provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Lưu video vào thư mục tạm thời
        fs = FileSystemStorage()
        filename = fs.save(video_file.name, video_file)
        video_path = os.path.join(settings.MEDIA_ROOT, filename)

        # Ghi video vào thư mục final với video_id
        video_info = {'video_id': filename.split('.')[0]}  # Giả sử video_id là tên file mà không có đuôi
        output_file = Path(os.path.join(settings.MEDIA_ROOT, 'final', f"{video_info['video_id']}.mp4"))

        # Tạo thư mục nếu nó không tồn tại
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Xử lý video với MoviePy
        try:
            # Tải video để xử lý
            final_video = VideoFileClip(video_path)
            final_video.write_videofile(output_file.as_posix(), codec="libx264", audio_codec="aac")
            logging.info(f"Generated output video: {output_file}")
            return Response({'message': 'Video uploaded and processed successfully!', 'video_path': output_file.as_posix()}, status=status.HTTP_201_CREATED)

        except Exception as e:
            logging.error(f"Có lỗi xảy ra khi ghi video: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'error': 'Invalid request method'}, status=status.HTTP_400_BAD_REQUEST)


class PreviewVideoView(APIView):
    def get(self, request, video_id):
        try:
            video_path = os.path.join(os.getcwd(), "static", "final", f"{video_id}.mp4")
            # Alternatively, if using MEDIA_ROOT:
            # video_path = Path(os.path.join(settings.MEDIA_ROOT, 'final', f"{video_id}.mp4"))

            if not os.path.exists(video_path):
                return Response({"detail": "Video not found"}, status=status.HTTP_404_NOT_FOUND)

            # Use StreamingHttpResponse to stream the video
            response = StreamingHttpResponse(open(video_path, 'rb'), content_type='video/mp4')
            response['Content-Length'] = os.path.getsize(video_path)  # Optional: set content length for better behavior
            return response
        except Exception as e:
            return Response({"detail": f"Error while trying to preview video: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

def process_background_music(request):
    print("=======>")
    textfile_id=1
    print("process_background_music")
    # Run process_video command in a new thread
    def run_process_command(textfile_id):
        try:
            call_command('music_processor', textfile_id)
        except Exception as e:
            # Handle the exception as needed (e.g., log it)
            print(f"Error processing video: {e}")

    
    
    textfile = TextFile.objects.get(pk=textfile_id)

    musics=textfile.background_musics.all()

    if request.method == 'POST':
        if textfile.background_musics:
            for bg in BackgroundMusic.objects.filter(text_file=textfile):
                bg.delete()
        try:
            # Fetch the TextFile instance
            if textfile.user != request.user:
                messages.error(request,'You Do Not have access to the Resources You Requested ')

                return render(request,'permission_denied.html')
        except TextFile.DoesNotExist:
            return Http404("Text file not found")
        no_of_mp3 = int(request.POST.get('no_of_mp3', 0))  # Number of MP3 files
    
        # Check if the necessary fields are present in TextFile
        if not textfile.text_file:
            return JsonResponse({"error": "Text file is missing."}, status=400)
        music_files = [request.FILES.get(f'bg_music_{i}') for i in range(1, no_of_mp3 +1)]  # Adjust based on your inputs
        start_times_str = {f'bg_music_{i}': request.POST.get(f'from_when_{i}') for i in range(1, no_of_mp3 +1)}
        bg_levels = {f'bg_music_{i}': float(request.POST.get(f'bg_level_{i}'))/1000.0 for i in range(1, no_of_mp3 +1)}
        end_times_str = {f'bg_music_{i}': request.POST.get(f'to_when_{i}') for i in range(1, no_of_mp3+1)}
        start_times = [convert_to_seconds(time_str) for time_str in start_times_str.values()]
        end_times = [convert_to_seconds(time_str) for time_str in end_times_str.values()]

        # Save music files and their paths
        music_paths = []
        bg_musics=[]
        for i, music_file in enumerate(music_files, start=1):
            if music_file:
                bg_music=BackgroundMusic(
                        text_file=textfile,
                        music=music_file,
                        start_time=start_times[i-1],
                        end_time=end_times[i-1],
                        bg_level=bg_levels[f"bg_music_{i}"]

                    )
                
                bg_musics.append(bg_music)
                # Perform bulk creation
        if bg_musics:
            BackgroundMusic.objects.bulk_create(bg_musics)

        lines = []
        for bg_music in bg_musics:
            start_time_str = bg_music.start_time
            end_time_str = bg_music.end_time
            bg_level=str(float(bg_music.bg_level))
            lines.append(f"{bg_music.music.name} {start_time_str} {end_time_str} {bg_level}")

        content = "\n".join(lines)
        
        # Save the content to a text file
        file_name = f'background_music_info_{textfile_id}_.txt'

        textfile.bg_music_text.save(file_name, ContentFile(content))
        # textfile.bg_level=float(request.POST.get('bg_level'))/100.0
        textfile.save()

        try:
            # call_command('music_processor', textfile_id)
            # # Start the background process/
            thread = threading.Thread(target=run_process_command, args=(textfile_id,))
            thread.start()
            return redirect(f'/text/progress_page/bg_music/{textfile_id}')


        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return render(request,'vlc/add_music.html',{'textfile_id':1,'textfile':textfile,'musics':musics})