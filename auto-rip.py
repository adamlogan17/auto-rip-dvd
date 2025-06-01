import copy
import os
import threading
import subprocess
import ctypes
from pathlib import Path
from dotenv import load_dotenv
from get_media_info import tmdb_movie_info, store_media_info, tmdb_tv_info
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
        highest_runtime = -1
        if 'TINFO' in info_type:
            title_id = info_title[1]
            info = processed_line[-1].strip('"')

            # Checks if the info is a runtime in the format HH:MM
            if re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', info):
                time_parts = info.split(':')
                if len(time_parts) == 3:
                    hours = int(time_parts[0])
                    minutes = int(time_parts[1])
                    runtime = (hours * 60) + minutes
                elif len(time_parts) == 2:
                    runtime = int(time_parts[0])
            if runtime >= (expected_runtime-runtime_threshold) and runtime <= (expected_runtime+runtime_threshold):
                print(f"Found matching runtime title: {title_id}, runtime: {runtime} minutes")
                return int(title_id)
            elif runtime > highest_runtime:
                highest_runtime = runtime
                backup_title_id = int(title_id)
    if highest_runtime > 0:
        print(f"No exact match found, using highest runtime title: {backup_title_id}, runtime: {highest_runtime} minutes")
        return backup_title_id

def convert_to_mkv_makemkv(output_dir, title_id, iso_filename, makemkv_cli_path=os.getenv('MAKEMKV', "C:\\Program Files (x86)\\MakeMKV\\makemkvcon")):
    mkv_command = [
        makemkv_cli_path,
        'mkv',
        f"file:{iso_filename}",
        f"{title_id}",
        output_dir,
        '--noscan'
    ]

    try:
        print(f"Starting MakeMKV decryption for disc:0...")
        subprocess.run(mkv_command, check=True)
        print(f"Decryption completed. Output saved to {output_dir}.")
    except FileNotFoundError:
        print("Error: MakeMKV not found. Please check the path to MakeMKV.")
    except subprocess.CalledProcessError as e:
        print(f"Error: MakeMKV failed with error code {e.returncode}.")

def get_title_info(iso_filename, makemkv_cli_path=os.getenv('MAKEMKV', "C:\\Program Files (x86)\\MakeMKV\\makemkvcon")):
    info_command = [
        makemkv_cli_path,
        'info',
        f"file:{iso_filename}",
        '--robot'
    ]

    try:
        print(f"Starting retrieving disc information using MakeMKV...")
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
        print(f"Starting MakeMKV decryption for disc:0...")
        subprocess.run(rip_command, check=True)
        print(f"Decryption completed. Output saved to {'output_file'}.")
    except FileNotFoundError:
        print("Error: MakeMKV not found. Please check the path to MakeMKV.")
    except subprocess.CalledProcessError as e:
        print(f"Error: MakeMKV failed with error code {e.returncode}.")

def convert_to_mp4_handbrake(input_file, output_file, title_id=None, handbrake_cli_path=os.getenv('HANDBRAKE', "C:\\Program Files\\HandBrake\\HandBrakeCLI.exe"), file_format="mp4"):
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
        command.extend(["--title", str(title_id+1)])

    try:
        # Run the HandBrakeCLI command
        print(f"Starting HandBrake encoding for {input_file}...")
        subprocess.run(command, check=True)
        print(f"Encoding completed. Output saved to {output_file}.")
    except FileNotFoundError:
        print("Error: HandBrakeCLI not found. Please check the path to HandBrakeCLI.")
    except subprocess.CalledProcessError as e:
        print(f"Error: HandBrakeCLI failed with error code {e.returncode}.")

def rip_dvd_title(iso_filename, mp4_output_folder, mkv_output_folder, title_id, file_name):
    mp4_name = Path(mp4_output_folder) / f"{file_name}.mp4"
    mkv_name = os.path.join(mkv_output_folder, f"{file_name}.mkv")
    mkv_started = False
    handbrake_started = False

    current_files = os.listdir(mkv_output_folder)

    mkv_thread = threading.Thread(
        target=convert_to_mkv_makemkv,
        args=(mkv_output_folder, title_id, iso_filename)
    )

    handbrake_thread = threading.Thread(
        target=convert_to_mp4_handbrake,
        args=(iso_filename, mp4_name),
        kwargs={'title_id': title_id}
    )

    # Start both threads
    if not os.path.exists(mkv_name):
        mkv_thread.start()
        mkv_started = True
    else:
        print(f"MKV file already exists: {mkv_name}")

    if not os.path.exists(mp4_name):
        handbrake_thread.start()
        handbrake_started = True
    else:
        print(f"MP4 file already exists: {mp4_name}")

    # Wait for both threads to complete
    if mkv_started:
        mkv_thread.join()
    if handbrake_started:
        handbrake_thread.join()

    updated_files = os.listdir(mkv_output_folder)
    new_file_name = list(set(updated_files) - set(current_files))
    if new_file_name:
        new_file_path = os.path.join(mkv_output_folder, new_file_name[0])
        mkv_name = os.path.join(mkv_output_folder, f"{file_name}.mkv")
        os.rename(new_file_path, mkv_name)

    if mkv_started and os.path.exists(mkv_name):
        print(f"MKV conversion completed: {mkv_name}")
    if handbrake_started and os.path.exists(mp4_name):
        print(f"MP4 conversion completed: {mp4_name}")

# NOTE: Need to split this function up, as it is too large
# NOTE: Add a check to see if the rip was successful and if so call store_media_info
def main(output_folders):
    # This is modified, if there is a tv show and therefore needs to be copied to ensure that thr argument is not modified
    out_folders = copy.deepcopy(output_folders)
    titles_to_rip = [] # NOTE: rename this variable, as it no longer holds the title id
    dvd_title = str(input('Title of DVD (Movie/TV Series Name): ')).strip()
    media_info = {}
    iso_name = ''

    # Handles DVDs with multiple episodes
    tv_show_input = str((input('Is this a TV show y/n: ')))
    if tv_show_input == 'y':
        # Get the media info from TMDB
        media_info = tmdb_tv_info(dvd_title)
        number_of_seasons = len(media_info['seasons'])
        print(f"This show has {number_of_seasons} season(s).")

        # Get user input for season and episode information
        season_number = 1
        if number_of_seasons > 1:
            season_number = int(input(f'Enter the season number for this disc (1-{number_of_seasons}): '))
        first_episode = int(input(f'Enter the first episode number: '))
        num_episodes = int((input('Enter the number of episodes on the disc: ')))

        # Adds a leading zero to the season and episode numbers for formatting (both Plex and Jellyfin use this format)
        formatted_season = f"{season_number:02d}"

        # Get the runtime and episode name for each episode on the disc
        for episode_number in range(first_episode, first_episode + num_episodes):
            # Need to subtract 1 to episode_number as the list is 0-indexed
            episode_info = media_info['seasons'][season_number-1]['episodes'][episode_number-1]
            formatted_episode = f"{episode_number:02d}"
            titles_to_rip.append(
                {
                    'file_name': f"{dvd_title} - s{formatted_season}e{formatted_episode} - {episode_info['episode_name']}",
                    'expected_runtime': episode_info['runtime']
                }
            )

        # 1 is subtracted, is because the 'first episode' is included in the count
        iso_name = f"{dvd_title} s{formatted_season}e{first_episode:02d} - e{((first_episode+num_episodes)-1):02d}"

        # Create the path for the tv show and seasons, based on the file structure provided by Plex and Jellyfin
        season_folder_name = f"Season {formatted_season}"

        # NOTE: Maybe have the dict as a user input and if one is missing, assume that it does not need to create the file for that
        # NOTE: For iso, if it is not present, just point it to the dvd drive directly
        for key in out_folders:
            out_folders[key] = Path(out_folders[key]) / dvd_title / season_folder_name
            out_folders[key].mkdir(parents=True, exist_ok=True)
    else:
        media_info = tmdb_movie_info(dvd_title)
        iso_name = dvd_title
        titles_to_rip.append(
            {
                'file_name': dvd_title,
                'expected_runtime': media_info['runtime']
            }
        )

    iso_filename = Path(out_folders['iso']) / f"{iso_name}.iso"

    encode = 'n' # Default to not encoding, if the user does not want to encode, then it will not start the decryption
    if not os.path.exists(iso_filename):
        encode = 'y'
        start_makemkv_decryption(iso_filename)
    else:
        print('Image already exists')
        encode = str(input('Proceed with encoding y/n: '))
        print('\nProcessing encoding, using existing ISO file.')

    if encode == 'y':
        # This is done after the user input, so the user does not have to wait for the decryption to start
        # This also means they can enter the required information and then leave
        disc_info = get_title_info(iso_filename)

        for title in titles_to_rip:
            title_id = -1 # Default to -1, prevents same title_id being used for multiple titles
            title_id = get_title_id(disc_info, title['expected_runtime'])
            if title_id == -1:
                print(f"Title ID not found for {title['file_name']}. Skipping encoding.")
            else:
                rip_dvd_title(iso_filename, out_folders['mp4'], out_folders['mkv'], title_id, title['file_name'])
    else:
        print("\nEncoding skipped.")

    if os.getenv('NO_EJECT') != True:
        store_media_info(media_info)
        eject_dvd()

if __name__ == '__main__':
    iso_out_dir = os.getenv('ISO_OUT_DIR', 'C:\\iso_movies\\')
    mp4_out_dir = os.getenv('MP4_OUT_DIR', 'C:\\mp4_movies\\')
    mkv_out_dir = os.getenv('MKV_OUT_DIR', 'C:\\mkv_movies\\')
    disc_drive = os.getenv('DISC_DRIVE', 'E:\\')

    output_folders = {
        'mp4': mp4_out_dir,
        'mkv': mkv_out_dir,
        'iso': iso_out_dir
    }

    while True:
        if dvd_detected(disc_drive):
            main(output_folders)