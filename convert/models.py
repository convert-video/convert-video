from django.db import models

# Create your models here.

from django.db import models
import uuid
import os

def upload_to(instance, filename):
    return os.path.join('uploads', f"{instance.id}", filename)

class VideoUpload(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to=upload_to)
    transcript = models.FileField(upload_to=upload_to)
    translation = models.FileField(upload_to=upload_to)
    font = models.FileField(upload_to=upload_to)
    font_size = models.IntegerField()
    font_color = models.CharField(max_length=7)  # e.g., "#FFFFFF"
    box_color = models.CharField(max_length=7)
    box_width = models.IntegerField()
    box_height = models.IntegerField()
    eleven_labs = models.CharField(max_length=255)
    voice_id = models.CharField(max_length=255)
    processed_video = models.FileField(upload_to='processed_videos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"VideoUpload {self.id}"
