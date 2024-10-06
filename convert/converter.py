import re
import logging
from pathlib import Path
from elevenlabs import Voice, VoiceSettings, save
from elevenlabs.client import ElevenLabs
from moviepy.editor import (
    AudioFileClip, ColorClip, CompositeAudioClip, CompositeVideoClip, concatenate_videoclips,
    TextClip, VideoFileClip, vfx, ImageClip
)
import tempfile
from pydub import AudioSegment
from moviepy.video.fx.crop import crop
from moviepy.video.fx.loop import loop
import pysrt
from PIL import Image, ImageDraw
import numpy as np
from moviepy.editor import ImageClip
from moviepy.config import change_settings
from typing import List, Tuple
from itertools import zip_longest
import os
import subprocess
import json
import sys

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG)
imagemagick_path = r"/usr/local/bin/magick" # update image magic path
UPLOAD_DIRECTORY = "uploads"
elevenlabs_api_key = "sk_38aae7d4c569725ebd7172864644e1780c42a55d7281cff5"  # ElevenLabs API key (take as input)
os.environ['IMAGEMAGICK_BINARY'] = imagemagick_path
change_settings({"IMAGEMAGICK_BINARY": imagemagick_path})

def replace_srt_text(original_srt_file, translated_file, translated_srt_file):
    # Read the SRT file
    with open(original_srt_file, 'r', encoding='utf-8') as srt:
        srt_lines = srt.readlines()

    # Read the translation file
    with open(translated_file, 'r', encoding='utf-8') as txt:
        translations = txt.readlines()

    # Initialize counters for SRT and translation lines
    srt_index = 0
    translation_index = 0

    # Open output file to write the result
    with open(translated_srt_file, 'w', encoding='utf-8') as output:
        while srt_index < len(srt_lines):
            line = srt_lines[srt_index].strip()

            # Check if the line contains a subtitle text (non-timestamp line)
            if "-->" not in line and line != '' and line.isdigit() is False:
                # Replace the English text with the translation from the txt file
                srt_lines[srt_index] = translations[translation_index]
                translation_index += 1

            # Write the line to the output file
            output.write(srt_lines[srt_index])
            output.write('')
            srt_index += 1

    print(f"Translated SRT saved as {translated_srt_file}")
def load_video_from_file(file: Path) -> VideoFileClip:
    # if not file.exists():
    #     raise FileNotFoundError(f"Video file not found: {file}")
    return VideoFileClip(file)


def crop_to_aspect_ratio(video: VideoFileClip, desired_aspect_ratio: float) -> VideoFileClip:
    video_aspect_ratio = video.w / video.h
    if video_aspect_ratio > desired_aspect_ratio:
        new_width = int(desired_aspect_ratio * video.h)
        new_height = video.h
        x1 = (video.w - new_width) // 2
        y1 = 0
    else:
        new_width = video.w
        new_height = int(video.w / desired_aspect_ratio)
        x1 = 0
        y1 = (video.h - new_height) // 2
    x2 = x1 + new_width
    y2 = y1 + new_height
    return crop(video, x1=x1, y1=y1, x2=x2, y2=y2)


def load_subtitles_from_file(srt_file: Path) -> pysrt.SubRipFile:
    # if not srt_file.exists():
    #     raise FileNotFoundError(f"SRT File not found: {srt_file}")
    return pysrt.open(srt_file)


def adjust_segment_duration(segment: VideoFileClip, duration: float) -> VideoFileClip:
    current_duration = segment.duration
    if current_duration < duration:
        return loop(segment, duration=duration)
    elif current_duration > duration:
        return segment.subclip(0, duration)
    return segment


def adjust_segment_properties(segment: VideoFileClip, original: VideoFileClip) -> VideoFileClip:
    segment = segment.set_fps(original.fps)
    segment = segment.set_duration(segment.duration)
    segment = segment.resize(newsize=(original.w, original.h))
    return segment


def subriptime_to_seconds(srt_time: pysrt.SubRipTime) -> float:
    return srt_time.hours * 3600 + srt_time.minutes * 60 + srt_time.seconds + srt_time.milliseconds / 1000.0


def get_segments_using_srt(video: VideoFileClip, subtitles: pysrt.SubRipFile):
    subtitle_segments = []
    video_segments = []
    video_duration = video.duration
    previous_end = 0.0

    for subtitle in subtitles:
        start = subriptime_to_seconds(subtitle.start)
        end = subriptime_to_seconds(subtitle.end)

        # If there's a gap between the previous end and the current start, add that segment
        if start > previous_end:
            logging.debug(f"Adding non-subtitled segment from {previous_end} to {start}")
            video_segment = video.subclip(previous_end, start)
            subtitle_segments.append(None)  # No subtitle for this segment
            video_segments.append(video_segment)

        # Adjust end time if it exceeds video duration
        if end > video_duration:
            logging.warning(f"Subtitle end time {end} exceeds video duration {video_duration}. Adjusting end time to video duration.")
            end = video_duration

        # Create the segment for the current subtitle
        if start < video_duration:
            logging.debug(f"Adding subtitled segment from {start} to {end}")
            video_segment = video.subclip(start, end)
            subtitle_segments.append(subtitle)
            video_segments.append(video_segment)
            previous_end = end

    # If there's any remaining video after the last subtitle, add it
    if previous_end < video_duration:
        logging.debug(f"Adding final non-subtitled segment from {previous_end} to {video_duration}")
        video_segment = video.subclip(previous_end, video_duration)
        subtitle_segments.append(None)
        video_segments.append(video_segment)

    logging.info(f"Total video segments: {len(video_segments)}")
    logging.info(f"Total subtitle segments: {len(subtitle_segments)}")

    return video_segments, subtitle_segments


def replace_audio_segment(video_segment: VideoFileClip, audio_segment: AudioSegment) -> VideoFileClip:
    video_duration = video_segment.duration
    audio_duration = audio_segment.duration_seconds

    logging.debug(f"Video duration: {video_duration}, Audio duration: {audio_duration}")

    if audio_duration != 0:
        video_segment = video_segment.fx(vfx.speedx, factor=video_duration / audio_duration)
    else:
        logging.error("Audio duration is zero, cannot change video speed")

    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio_file:
        audio_segment.export(temp_audio_file.name, format="mp3")
        new_audio_clip = AudioFileClip(temp_audio_file.name).set_duration(video_segment.duration)

    return video_segment.set_audio(new_audio_clip)


def create_rounded_rectangle(w, h, radius):
    """Creates a rounded rectangle mask using PIL."""
    image = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle([(0, 0), (w, h)], radius, fill=(255, 255, 255, 255))
    mask = np.array(image)
    mask = mask[:, :, 3] / 255.0
    return mask


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

def add_subtitles_to_clip(
        clip: VideoFileClip, 
        subtitle: pysrt.SubRipItem, 
        font_path: str,
        box_color: str,
        font_size,
        color: str = "white",
        box_size: Tuple[int, int] = (800, 100), 
        margin_bottom: int = 20
    ) -> VideoFileClip:

    if subtitle is None:
        return clip  # No subtitle to add
    logging.info(f"Adding subtitle: {subtitle.text}")
    font_path = os.path.join(os.getcwd(), font_path)

    # Extract box size (width and height)
    box_width, box_height = box_size

    # Ensure the box stays centered horizontally at the bottom of the screen with a 20-pixel margin
    video_center_x = clip.w / 2
    box_x = video_center_x - (box_width / 2)
    box_y = clip.h - box_height - margin_bottom

    # Create the subtitle text clip
    subtitle_clip = TextClip(
        subtitle.text,
        fontsize=font_size,
        color=color,
        stroke_color="white",
        stroke_width=1,
        font=font_path,
        method='caption',
        align='center',
        size=(box_width, None)  # Width is fixed, height will adjust based on the text
    ).set_duration(clip.duration)  # Set duration to match the clip's duration

    # Calculate the vertical position of the text within the box
    text_width, text_height = subtitle_clip.size
    subtitle_position = (box_x, box_y + (box_height - text_height) / 2)
    box_color = hex_to_rgb(box_color)

    # Create the box with rounded corners
    radius = 1  # Adjust this value to change the roundness
    box_mask_array = create_rounded_rectangle(box_width, box_height, radius)

    # Create the ColorClip with rounded corners mask
    box_clip = ColorClip(size=(box_width, box_height), color=box_color).set_opacity(1).set_duration(clip.duration)
    box_clip = box_clip.set_mask(ImageClip(box_mask_array, ismask=True))

    # Set positions for the box and the subtitle clips
    box_clip = box_clip.set_position((box_x, box_y))
    subtitle_clip = subtitle_clip.set_position(subtitle_position)

    # Composite the video, box, and subtitle clips together
    return CompositeVideoClip([clip, box_clip, subtitle_clip])

def convert_mp4_to_mp3(input_video_file, mp3_file):
    # Load the video file
    video_clip = VideoFileClip(input_video_file)

    # Extract audio from the video
    audio_clip = video_clip.audio

    # Write the audio to an mp3 file
    audio_clip.write_audiofile(mp3_file)

    # Close the audio and video clips
    audio_clip.close()
    video_clip.close()
#
# def main():
#     video_info = {
#             "video_location": ",
#             "transcript_location": transcript_location,
#             "translation_location": translation_location,
#             "font_location": font_location,
#             "font_size": font_size,
#             "font_color": font_color,
#             "box_color": box_color,
#             "box_size": box_size
#     }
#     process_video()

def process_video(video_info):

    print("---video infomation--->")
    print(video_info)

    client = ElevenLabs(api_key=video_info["eleven_labs"])
    translated_srt_file = os.path.join(os.getcwd(), 'tmp', "VSL1_with_timestamps - Copy.srt") # this file will be generated by the code
    input_video_file = os.path.join(os.getcwd(), video_info["video_location"])
    # input_video_file = f"/home/neymarsabin/bucks/work/movieconverter/drycloud.mp4"
    mp3_file = os.path.join(os.getcwd(), 'tmp', 'output_audio.mp3')  # Replace with your desired MP3 output path
    translated_file = os.path.join(os.getcwd(), video_info["translation_location"]) 
    # translated_file = r"/home/neymarsabin/bucks/work/movieconverter/translated.txt"  # Replace with your actual translated TXT file path
    replacement_audio_folder = os.path.join(os.getcwd(), 'tmp', 'audios') # audios generated by 11 labs will be saved in this folder
    # output_folder = Path(r"output")
    convert_mp4_to_mp3(input_video_file, mp3_file) # command line that converts video into mp3 audio
    txt_file = os.path.join(os.getcwd(), video_info["transcript_location"])
    # txt_file = r"/home/neymarsabin/bucks/work/movieconverter/vsl1.txt" # modify code to take txt file(english subtitle file) as input
    output_json_path = txt_file.replace(".txt", "_aligned.json")

    # Generate the sync map using aeneas CLI
    command = f'python -m aeneas.tools.execute_task "{mp3_file}" "{txt_file}" "task_language=eng|is_text_type=plain|os_task_file_format=json" "{output_json_path}"'
    print("Running command:", command)
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Check the output and error of the command
    print("Command output:", result.stdout.decode('utf-8'))
    print("Command error:", result.stderr.decode('utf-8'))

    # Verify if the output file was created
    if not os.path.exists(output_json_path):
        raise FileNotFoundError(
            f"The output file {output_json_path} was not created. Check the command output above for errors.")

    # Read and parse the output file
    with open(output_json_path, 'r') as f:
        sync_map = json.load(f)

    # Convert seconds to hours:minutes:seconds,milliseconds format
    def convert_time(seconds):
        milliseconds = int((seconds - int(seconds)) * 1000)
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

    # Process the output to make it SRT readable
    aligned_output = []
    for index, fragment in enumerate(sync_map['fragments']):
        start = convert_time(float(fragment['begin']))
        end = convert_time(float(fragment['end']))
        text = fragment['lines'][0].strip()
        aligned_output.append(f"{index + 1}\n{start} --> {end}\n{text}\n")

    # Write output to a new text file in SRT format
    original_srt_file = txt_file.replace(".txt", "_with_timestamps.srt")
    with open(original_srt_file, 'w') as file:
        for line in aligned_output:
            file.write(line + "\n")

    # Convert SRT to JSON format
    srt_json = []
    for index, fragment in enumerate(sync_map['fragments']):
        start = float(fragment['begin'])
        end = float(fragment['end'])
        text = fragment['lines'][0].strip()
        srt_json.append({
            "index": index + 1,
            "start": start,
            "end": end,
            "text": text
        })

    # Write the JSON output to a new file
    srt_json_file = original_srt_file.replace(".srt", ".json")
    with open(srt_json_file, 'w') as file:
        json.dump(srt_json, file, indent=4)


    print("===>")
    print(original_srt_file)
    print("===>")
    print(translated_file)
    print("===>")

    print(translated_srt_file)
    
    replace_srt_text(original_srt_file, translated_file, translated_srt_file)
# this part generates audio segments
    os.makedirs(replacement_audio_folder, exist_ok=True)

    # Function to save audio data to a file
    def save_audio(audio_data, filename):
        with open(filename, "wb") as f:
            f.write(audio_data)
        print(f"Audio saved to: {filename}")

    # Function to extract text lines from an SRT block
    def extract_text_from_srt_block(block):
        lines = block.strip().split('\n')[2:]  # Skip the index and timestamp lines
        return ' '.join(lines)

    # Read SRT content from the input file
    try:
        with open(translated_srt_file, "r", encoding="utf-8") as input_file:
            srt_content = input_file.read()
    except FileNotFoundError:
        print(f"Error: Input file '{translated_srt_file}' not found.")
        exit(1)

    # Split the SRT content into blocks
    srt_blocks = re.split(r'\n\n+', srt_content.strip())

    # Iterate over each SRT block, generate audio, and save it
    for block in srt_blocks:
        block_lines = block.strip().split('\n')
        segment_index = block_lines[0]  # Get the segment index
        text_to_speak = extract_text_from_srt_block(block)  # Extract the text to be spoken

        # Generate voice from the extracted text
        try:
            audio_data = client.generate(
                text=text_to_speak,
                voice=Voice(
                    voice_id=video_info["voice_id"], # modify code to take voice id as input
                    settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
                )
            )

            # Define the output file path
            output_file_path = os.path.join(replacement_audio_folder, f"segment_{segment_index}.mp3")

            # Save the audio to a file
            save(audio_data, output_file_path)

        except Exception as e:
            print(f"An error occurred while generating audio for segment {segment_index}: {e}")

    print("All segments have been processed and saved.")


    # output_folder.mkdir(parents=True, exist_ok=True)

    video = load_video_from_file(input_video_file)
    logging.info("Video loaded successfully")
    cropped_video = crop_to_aspect_ratio(video, 4 / 5)
    logging.info("Video cropped to desired aspect ratio")
    subtitles = load_subtitles_from_file(translated_srt_file)
    logging.info("Loaded SRT Subtitles from the provided subtitle file")
    old_subtitles = load_subtitles_from_file(translated_srt_file)
    logging.info("Loaded old SRT Subtitles from the provided subtitle file")
    video_segments, subtitle_segments = get_segments_using_srt(video, subtitles)
    old_video_segments, old_subtitle_segments = get_segments_using_srt(video, old_subtitles)
    logging.info("Segmented Input video based on the SRT Subtitles generated for it")

    # Log the number of segments
    logging.info(f"Total video segments: {len(video_segments)}")
    logging.info(f"Total subtitle segments: {len(subtitle_segments)}")
    logging.info(f"Total old subtitle segments: {len(old_subtitle_segments)}")

    # Use zip_longest to ensure all segments are processed
    for i, (video_segment, subtitle, old_subtitle) in enumerate(
            zip_longest(video_segments, subtitle_segments, old_subtitle_segments), start=1):
        audio_file_path = Path(f"{replacement_audio_folder}/segment_{i}.mp3")
        if audio_file_path.exists():
            logging.info(f"Replacing audio for segment {i} with {audio_file_path}")
            audio_segment = AudioSegment.from_file(audio_file_path)
            video_segment = replace_audio_segment(video_segment, audio_segment)
        else:
            # Since audio files start at 1, log accordingly
            logging.warning(f"Audio file not found for segment {i}: {audio_file_path}. Using original audio.")

        # Assume standard position for old subtitles
        box_width = video_info["box_width"]
        box_height = video_info["box_height"]
        box_dimensions = (box_width, box_height) # box width and height coming from input
        video_segment = add_subtitles_to_clip(
            video_segment, 
            subtitle, 
            video_info["font_location"], 
            video_info["box_color"], 
            video_info["font_size"],
            video_info["font_color"],
            box_dimensions 
        )
        video_segments[i-1] = video_segment  # Assign back to the correct index

    final_video = concatenate_videoclips(video_segments)

    video_id = video_info["video_id"]
    output_file = Path(os.path.join(os.getcwd(), 'static', 'final', f"{video_id}.mp4"))
    final_video.write_videofile(output_file.as_posix(), codec="libx264", audio_codec="aac")
    logging.info(f"Generated output video: {output_file}")
