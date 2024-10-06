from django.http import JsonResponse
from moviepy.editor import TextClip
import os
import logging
from django.conf import settings

def create_text_clip(subtitle_text: str, fontsize: int, color: str, stroke_color: str, stroke_width: int, font_path: str, box_width: int) -> TextClip:
    """Creates a TextClip with the specified parameters."""
    try:
        text_clip = TextClip(
            subtitle_text,
            fontsize=fontsize,
            color=color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            font=font_path,
            method='caption',
            align='center',
            size=(box_width, None)  # Width is fixed, height will adjust based on the text
        ).set_duration(5)  # Set duration for the text clip

        return text_clip

    except Exception as e:
        logging.error(f"Error creating text clip: {e}")
        raise

def generate_video_test():
    """Generates a video with subtitles using MoviePy."""
    # Set ImageMagick path
    imagemagick_path = "/usr/local/bin/magick"
    os.environ['IMAGEMAGICK_BINARY'] = imagemagick_path

    # Ensure the font file exists
    font_path = os.path.join(settings.MEDIA_ROOT, 'Select Font File.ttf')
    logging.debug(f"Font path: {font_path}")

    if not os.path.isfile(font_path):
        return JsonResponse({'error': 'Font file not found'}, status=400)

    # Parameters for the text clip
    subtitle_text = "jkjkjkjkjkj"
    fontsize = 70
    color = "white"
    stroke_color = "black"  # Stroke color
    stroke_width = 2  # Stroke width
    box_width = 800

    # Create a TextClip
    try:
        text_clip = create_text_clip(
            subtitle_text,
            fontsize,
            color,
            stroke_color,
            stroke_width,
            font_path,
            box_width
        )

        # Create a short video with the text
        video_path = os.path.join(settings.MEDIA_ROOT, 'generated_video-1.mp4')
        text_clip.write_videofile(video_path, fps=24)

        return video_path
        return JsonResponse({'message': 'Video generated successfully!', 'video_path': video_path}, status=200)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return JsonResponse({'error': str(e)}, status=500)
