# converterapp/serializers.py

from rest_framework import serializers
from .models import VideoUpload

class VideoUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoUpload
        fields = [
            'id',
            'file',
            'transcript',
            'translation',
            'font',
            'font_size',
            'font_color',
            'box_color',
            'box_width',
            'box_height',
            'eleven_labs',
            'voice_id',
            'processed_video',
            'created_at',
        ]
        read_only_fields = ['id', 'processed_video', 'created_at']
