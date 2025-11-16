import os
import time
import math
import ffmpeg
from faster_whisper import WhisperModel

def format_input_video_name(file_path):
    """Formats the input video name by replacing spaces with hyphens and converting to lowercase.

    Args:
        input_video (str): The name of the input video file.

    Returns:
        str: The formatted video name.
    """
    dir = file_path.split('/')
    input_video = dir[-1]
    file_path = '/'.join(dir[:-1])
    return {
        'file_path': file_path,
        'video_name': input_video.split('.')[0].replace(" ", "-").lower()
    }

# NOTE: This requires 'brew install ffmpeg' so need to make a docker container for this script
def extract_audio(input_video):
    """Extracts audio from a video file using ffmpeg.

    Args:
        input_video (str): The path to the input video file.

    Returns:
        str: The path to the extracted audio file.
    """
    formatted_path = format_input_video_name(input_video)
    extracted_audio = f"{formatted_path['file_path']}/audio-{formatted_path['video_name']}.wav"
    stream = ffmpeg.input(input_video)
    stream = ffmpeg.output(stream, extracted_audio)
    ffmpeg.run(stream, overwrite_output=True)
    return extracted_audio

def transcribe(audio):
    """Transcribes an audio file using the Whisper ASR model.

    Args:
        audio (str): The path to the audio file.

    Returns:
        tuple: A tuple containing the detected language (str) and a list of transcribed segments.
    """
    model = WhisperModel("small")
    segments, info = model.transcribe(audio)
    language = info.language
    print("Transcription language", language)
    segments = list(segments)
    print(segments)
    for segment in segments:
        print(f"[{segment.start}s -> {segment.end}s] {segment.text}")
    return language, segments

def format_time(seconds):
    """Formats seconds into a time string (HH:MM:SS,ms).

    Args:
        seconds (float): The time in seconds.

    Returns:
        str: The formatted time string.
    """
    hours = math.floor(seconds / 3600)
    seconds %= 3600
    minutes = math.floor(seconds / 60)
    seconds %= 60
    milliseconds = round((seconds - math.floor(seconds)) * 1000)
    seconds = math.floor(seconds)
    formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:01d},{milliseconds:03d}"
    return formatted_time

def generate_subtitle_file(language, segments, input_video):
    """Generates a subtitle file (.srt) from transcribed segments.

    Args:
        language (str): The language of the subtitles.
        segments (list): A list of transcribed segments from whisper.
        input_video (str): The name of the input video file.

    Returns:
        str: The path to the generated subtitle file.
    """
    formatted_path = format_input_video_name(input_video[-1])
    subtitle_file = f"{formatted_path['file_path']}/sub-{formatted_path['video_name']}.{language}.srt"
    text = ""
    for index, segment in enumerate(segments):
        segment_start = format_time(segment.start)
        segment_end = format_time(segment.end)
        text += f"{str(index+1)} \n"
        text += f"{segment_start} --> {segment_end} \n"
        text += f"{segment.text} \n"
        text += "\n"
        
    f = open(subtitle_file, "w")
    f.write(text)
    f.close()
    return subtitle_file

def add_subtitle_to_video(input_video, subtitle_file, soft_subtitle=True, overwrite_input=True):
    """Adds a subtitle file to a video file.

    Args:
        input_video (str): The path to the input video file.
        subtitle_file (str): The path to the subtitle file.
        soft_subtitle (bool, optional): If True, adds the subtitle as a separate track. 
                                        If False, burns the subtitle into the video. 
                                        Defaults to True.
        overwrite_input (bool, optional): If True, creates a new output file instead of 
                                        overwriting the input. Defaults to True.
    """
    subtitle_language = subtitle_file.split(".")[-2]
    input_video_name = format_input_video_name(input_video)
    video_input_stream = ffmpeg.input(input_video)
    subtitle_input_stream = ffmpeg.input(subtitle_file)
    if overwrite_input:
        output_video = f"~/Movies/{input_video_name}.mp4"
    subtitle_track_title = subtitle_file.replace(".srt", "")

    # A 'soft subtitle' adds the subtitle as a separate track in the video file, which can be turned on or off by the user.
    # A 'hard subtitle' burns the subtitle into the video, which cannot be turned off
    if soft_subtitle:
        stream = ffmpeg.output(
            video_input_stream, subtitle_input_stream, output_video, **{"c": "copy", "c:s": "mov_text"},
            **{"metadata:s:s:0": f"language={subtitle_language}",
            "metadata:s:s:0": f"title={subtitle_track_title}"}
        )
        ffmpeg.run(stream, overwrite_output=True)
    else:
        stream = ffmpeg.output(video_input_stream, output_video, vf=f"subtitles={subtitle_file}")

        ffmpeg.run(stream, overwrite_output=True)

if __name__ == "__main__":
    dir = '/Volumes/NO NAME'

    for input_file in os.listdir(dir):
        print(f"Processing file: {input_file}")
        format = format_input_video_name(input_file)
        audio = f"{format['file_path']}/audio-{format['video_name']}.wav"
        sub = f"{format['file_path']}/sub-{format['video_name']}.en.srt"
        if '.mp4' in input_file and 'john wick' not in input_file.lower():
            input_file = os.path.join(dir, input_file)
            if not os.path.exists(audio):
                audio = extract_audio(input_file)
            language, segments = transcribe(audio=audio)
            if not os.path.exists(sub):
                subtitle_file = generate_subtitle_file(language, segments, input_file)
            print(f"Subtitle file generated: {subtitle_file}")
            add_subtitle_to_video(input_file, subtitle_file, soft_subtitle=True)

