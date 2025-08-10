import time
import math
import ffmpeg
from faster_whisper import WhisperModel

def format_input_video_name(input_video):
    return input_video.split('.')[0].replace(" ", "-").lower()

# NOTE: This requires 'brew install ffmpeg' so need to make a docker container for this script
def extract_audio(input_video):
    input_video_name = format_input_video_name(input_video)
    extracted_audio = f"audio-{input_video_name}.wav"
    stream = ffmpeg.input(input_video)
    stream = ffmpeg.output(stream, extracted_audio)
    ffmpeg.run(stream, overwrite_output=True)
    return extracted_audio

def transcribe(audio):
    model = WhisperModel("small")
    segments, info = model.transcribe(audio)
    language = info.language
    print("Transcription language", language)
    segments = list(segments)
    print(segments)
    for segment in segments:
        # print(segment)
        print(f"[{segment.start}s -> {segment.end}s] {segment.text}")
    return language, segments

def format_time(seconds):
    hours = math.floor(seconds / 3600)
    seconds %= 3600
    minutes = math.floor(seconds / 60)
    seconds %= 60
    milliseconds = round((seconds - math.floor(seconds)) * 1000)
    seconds = math.floor(seconds)
    formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:01d},{milliseconds:03d}"
    return formatted_time

def generate_subtitle_file(language, segments, input_video):
    input_video_name = format_input_video_name(input_video)
    subtitle_file = f"sub-{input_video_name}.{language}.srt"
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

if __name__ == "__main__":
    input_file = "Italian Job.mp4"
    audio = extract_audio(input_file)
    language, segments = transcribe(audio=audio)
    subtitle_file = generate_subtitle_file(language, segments, input_file)
    print(f"Subtitle file generated: {subtitle_file}")

