# Generated by Django 3.2.25 on 2024-10-12 09:52

import convert.models
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='VideoUpload',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('file', models.FileField(upload_to=convert.models.upload_to)),
                ('transcript', models.FileField(upload_to=convert.models.upload_to)),
                ('translation', models.FileField(upload_to=convert.models.upload_to)),
                ('font', models.FileField(upload_to=convert.models.upload_to)),
                ('font_size', models.IntegerField()),
                ('font_color', models.CharField(max_length=7)),
                ('box_color', models.CharField(max_length=7)),
                ('box_width', models.IntegerField()),
                ('box_height', models.IntegerField()),
                ('eleven_labs', models.CharField(max_length=255)),
                ('voice_id', models.CharField(max_length=255)),
                ('processed_video', models.FileField(blank=True, null=True, upload_to='processed_videos/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
