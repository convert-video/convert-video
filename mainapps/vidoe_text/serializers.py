# serializers.py
from rest_framework import serializers

class BackgroundMusicSerializer(serializers.Serializer):
    no_of_mp3 = serializers.IntegerField()
    bg_music = serializers.FileField(required=False)
    from_when = serializers.CharField(max_length=8)  # HH:MM:SS format
    bg_level = serializers.FloatField()
    to_when = serializers.CharField(max_length=8)  # HH:MM:SS format
    
    # bg_music_2 = serializers.FileField(required=False)
    # from_when_2 = serializers.CharField(max_length=8)  # HH:MM:SS format
    # bg_level_2 = serializers.FloatField()
    # to_when_2 = serializers.CharField(max_length=8)  # HH:MM:SS format
