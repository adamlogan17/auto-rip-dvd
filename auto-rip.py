import os
import threading
import time
import subprocess
import ctypes
from pathlib import Path
from dotenv import load_dotenv
from get_movie_info import tmdb_info, store_movie_info
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

def get_title_id(makemkv_info, expected_runtime, runtime_threshold=10):
    print(f"Looking for runtime: {expected_runtime} minutes")
    
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
            if runtime >= (expected_runtime-runtime_threshold) and runtime <= (expected_runtime+runtime_threshold):
                print(f"Found matching runtime title:{title_id}, runtime: {runtime} minutes")
                return int(title_id)

def start_mkv_using_disc(output_dir, title_id, makemkv_cli_path=os.getenv('MAKEMKV', "C:\\Program Files (x86)\\MakeMKV\\makemkvcon")):
    mkv_command = [
        makemkv_cli_path,
        'mkv',
        'disc:0', # is whatever is in the disc drive (may need to change index, if multiple drive). Possible solution is to use the 'file:<>' option and point to 'E:'
        f"{title_id}",
        output_dir,
        '--noscan'
    ]

    print(mkv_command)

    try:
        print(f"Starting MakeMKV decryption for disc:0...")
        subprocess.run(mkv_command, check=True)
        print(f"Decryption completed. Output saved to {output_dir}.")
    except FileNotFoundError:
        print("Error: MakeMKV not found. Please check the path to MakeMKV.")
    except subprocess.CalledProcessError as e:
        print(f"Error: MakeMKV failed with error code {e.returncode}.")

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

def main(iso_output_folder, mp4_output_folder, mkv_output_folder, disc_drive):
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
            movie_info = tmdb_info(dvd_title)
            store_movie_info(movie_info)
            title_id = get_title_id(disc_info, movie_info['runtime'])
            if title_id == -1:
                start_handbrake_encode(iso_filename, mp4_name)
            else:
                current_files = os.listdir(mkv_output_folder)
                mkv_thread = threading.Thread(
                    target=start_mkv_using_disc,
                    args=(mkv_output_folder, title_id)
                )
                handbrake_thread = threading.Thread(
                    target=start_handbrake_encode,
                    args=(iso_filename, mp4_name),
                    kwargs={'title_id': title_id}
                )

                # Start both threads
                mkv_thread.start()
                handbrake_thread.start()

                # Wait for both threads to complete
                mkv_thread.join()
                handbrake_thread.join()

                updated_files = os.listdir(mkv_output_folder)
                new_file_name = list(set(updated_files) - set(current_files))
                if new_file_name:
                    new_file_path = os.path.join(mkv_out_dir, new_file_name[0])
                    new_name = os.path.join(mkv_out_dir, f"{dvd_title}.mkv")
                    os.rename(new_file_path, new_name)
        eject_dvd()

if __name__ == '__main__':
    iso_out_dir = os.getenv('ISO_OUT_DIR', 'C:\\iso_movies\\')
    mp4_out_dir = os.getenv('MP4_OUT_DIR', 'C:\\mp4_movies\\')
    mkv_out_dir = os.getenv('MKV_OUT_DIR', 'C:\\mkv_movies\\')
    disc_drive = os.getenv('DISC_DRIVE', 'E:\\')

    while True:
        main(iso_out_dir, mp4_out_dir, mkv_out_dir, disc_drive)