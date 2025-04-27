import os
import time
import subprocess
import ctypes
from pathlib import Path
from dotenv import load_dotenv
from get_movie_info import tmdb_info
import re

load_dotenv()

# Handbrake CLI, can be found at this link https://handbrake.fr/downloads2.php

def eject_dvd():
    print('Ejecting DVD!')
    try:
        ctypes.windll.WINMM.mciSendStringW(u"set cdaudio door open",None,0,None)
    except:
        os.system("eject cdrom")

def dvd_detected(drive_path):
    """
    Checks if a DVD is detected in the specified drive.

    :param drive_path: The path to the disc drive
    :return: True if a DVD is detected, False otherwise.
    """
    return os.path.exists(drive_path) and os.path.isdir(drive_path)

def get_title_id(makemkv_info, movie_title, runtime_threshold=10):
    tmdb_runtime = tmdb_info(movie_title)['runtime']

    print(f"TMDB runtime for {movie_title}: {tmdb_runtime} minutes")
    
    for line in makemkv_info.splitlines():
        processed_line = line.split(',')
        info_title = processed_line[0].split(':')
        info_type = info_title[0]
        runtime = -1
        if 'TINFO' in info_type:
            title_id = info_title[1]
            info = processed_line[-1].strip('"')
            if re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', info):
                time_parts = info.split(':')
                if len(time_parts) == 3:
                    hours = int(time_parts[0])
                    minutes = int(time_parts[1])
                    runtime = (hours * 60) + minutes
                elif len(time_parts) == 2:
                    runtime = int(time_parts[0])
            if runtime >= (tmdb_runtime-runtime_threshold) and runtime <= (tmdb_runtime+runtime_threshold):
                print(f"Found matching runtime for {movie_title}: title:{title_id}, runtime: {runtime} minutes")
                return int(title_id)

def get_title_info(makemkv_cli_path=os.getenv('MAKEMKV', "C:\\Program Files (x86)\\MakeMKV\\makemkvcon")):
    info_command = [
        makemkv_cli_path,
        'info',
        'disc:0',
        '--robot'
    ]

    try:
        print(f"Starting MakeMKV decryption for disc:0 ...")
        disc_info = subprocess.run(info_command, check=True, text=True, capture_output=True)
        print(f"Decryption completed. Output saved to {'output_file'}.")
        return disc_info.stdout
    except FileNotFoundError:
        print("Error: MakeMKV not found. Please check the path to MakeMKV.")
    except subprocess.CalledProcessError as e:
        print(f"Error: MakeMKV failed with error code {e.returncode}.")

def start_makemkv_decryption(output_dir, makemkv_cli_path=os.getenv('MAKEMKV', "C:\\Program Files (x86)\\MakeMKV\\makemkvcon")):
    rip_command = [
        makemkv_cli_path,
        'backup',
        'disc:0', # is whatever is in the disc drive (may need to change index, if multiple drive). Possible solution is to use the 'file:<>' option and point to 'E:'
        output_dir,
        '--noscan',
        '--decrypt'
    ]

    try:
        print(f"Starting MakeMKV decryption for {'input_file'}...")
        subprocess.run(rip_command, check=True)
        print(f"Decryption completed. Output saved to {'output_file'}.")
    except FileNotFoundError:
        print("Error: MakeMKV not found. Please check the path to MakeMKV.")
    except subprocess.CalledProcessError as e:
        print(f"Error: MakeMKV failed with error code {e.returncode}.")

def is_file_detected(folder_path, interval=1):
    """
    Monitors a folder and returns True if a new file is added.

    :param folder_path: Path to the folder to monitor.
    :param interval: Time interval (in seconds) to check for changes.
    :return: True if a new file is added, False otherwise.
    """
    # Get the initial list of files in the folder
    previous_files = set(os.listdir(folder_path))

    while True:
        time.sleep(interval)  # Wait for the specified interval
        current_files = set(os.listdir(folder_path))  # Get the current list of files

        # Check if there are any new files
        if current_files - previous_files:
            return True

        # Update the previous state
        previous_files = current_files

def start_handbrake_encode(input_file, output_file, title_id=None, handbrake_cli_path=os.getenv('HANDBRAKE', "C:\\Program Files\\HandBrake\\HandBrakeCLI.exe"), file_format="mp4"):
    """
    Automatically starts HandBrake encoding with the preset 'Fast 1080p30'.

    :param input_file: Path to the input video file.
    :param output_file: Path to the output encoded video file.
    """

    # HandBrakeCLI command with the 'Fast 1080p30' preset
    # The preset does not upscale, this is an upper limit of quality
    command = [
        handbrake_cli_path,
        "-i", input_file,
        "-o", output_file,
        # "-f", f"av_{file_format}",
        "--preset", "Fast 1080p30"
    ]

    if title_id:
        command.extend(["--title", title_id+1])

    try:
        # Run the HandBrakeCLI command
        print(f"Starting HandBrake encoding for {input_file}...")
        subprocess.run(command, check=True)
        print(f"Encoding completed. Output saved to {output_file}.")
    except FileNotFoundError:
        print("Error: HandBrakeCLI not found. Please check the path to HandBrakeCLI.")
    except subprocess.CalledProcessError as e:
        print(f"Error: HandBrakeCLI failed with error code {e.returncode}.")

def main(iso_output_folder, mp4_output_folder, disc_drive):
    if dvd_detected(disc_drive):
        dvd_title = str(input('Title of DVD: '))

        # Handles DVDs with multiple episodes
        tv_show_input = str((input('Is this a TV show y/n: ')))
        if tv_show_input == 'y':
            num_episodes = int((input('Enter the number of episodes on the disc: ')))

        iso_filename = Path(iso_output_folder) / f"{dvd_title}.iso"

        mp4_name = Path(mp4_output_folder) / f"{dvd_title}.mp4"

        if not os.path.exists(iso_filename):
            encode = 'y'
            disc_info = get_title_info()
            start_makemkv_decryption(iso_filename)
        else:
            print('Image already exists')
            encode = str(input('Proceed with encoding y/n: '))

        if encode == 'y':
            title_id = get_title_id(disc_info, dvd_title)
            if title_id == -1:
                start_handbrake_encode(iso_filename, mp4_name)
            else:
                start_handbrake_encode(iso_filename, mp4_name, title_id=title_id)

        # NOTE: Add code to eject the 'drive' that is created with the movie in MakeMKV
        eject_dvd()

if __name__ == '__main__':
    iso_out_dir = os.getenv('ISO_OUT_DIR', 'C:\\iso_movies\\')
    mp4_out_dir = os.getenv('MP4_OUT_DIR', 'C:\\mp4_movies\\')
    disc_drive = os.getenv('DISC_DRIVE', 'E:\\')
    while True:
        main(iso_out_dir, mp4_out_dir, disc_drive)