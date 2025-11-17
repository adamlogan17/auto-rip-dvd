import copy
import os
import threading
import ctypes
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict
from application.Handbrake import Handbrake
from application.MakeMKV import MakeMKV
from application.VideoRipApp import VideoRipApp, TitleInfo
from get_media_info import tmdb_movie_info, store_media_info, tmdb_tv_info
from typing import List

# TODO Try and find a better name for this
class RipApps(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    app: VideoRipApp
    title_info: List[TitleInfo]
    name: str

load_dotenv()

# Handbrake CLI, can be found at this link https://handbrake.fr/downloads2.php

def eject_dvd():
    print('Ejecting DVD!')
    try:
        ctypes.windll.WINMM.mciSendStringW(u"set cdaudio door open",None,0,None) # pyright: ignore[reportAttributeAccessIssue] - states that 'ctypes' has no attribute 'windll', but it does 
    except:
        os.system("eject cdrom")

def dvd_detected(drive_path):
    """
    Checks if a DVD is detected in the specified drive.

    :param drive_path: The path to the disc drive
    :return: True if a DVD is detected, False otherwise.
    """
    return os.path.exists(drive_path) and os.path.isdir(drive_path) and os.listdir(drive_path) != []

def write_to_file(file_path, content):
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Content written to {file_path}")
    except Exception as e:
        print(f"Error writing to file {file_path}: {e}")

def console_user_input():
    tv_show_info = None

    dvd_title = str(input('Title of DVD (Movie/TV Series Name): ')).strip()

    special_feature_input = str(input('Is this a special features disc? y/n: ')).strip().lower()
    special_feature = special_feature_input == 'y'

    tv_show_input = str((input('Is this a TV show? y/n: '))).strip().lower()
    
    if tv_show_input == 'y':
        season_number = 0
        first_episode = 0
        num_episodes = 0

        if special_feature_input != 'y':
            season_number = int(input(f'Enter the season number for this disc: ').strip())
            first_episode = int(input(f'Enter the first episode number: ').strip())
            num_episodes = int((input('Enter the number of episodes on the disc: ')).strip())

        tv_show_info = {
            'season_number': season_number,
            'first_episode': first_episode,
            'num_episodes': num_episodes
        }

    return {
        'dvd_title': dvd_title,
        'tv_show': tv_show_info,
        'special_feature': special_feature
    }

# NOTE: Need to split this function up, as it is too large
# NOTE: Add a check to see if the rip was successful and if so call store_media_info
def main(output_folders, user_config):
    # This is modified, if there is a tv show and therefore needs to be copied to ensure that thr argument is not modified
    out_folders = copy.deepcopy(output_folders)
    titles_to_rip = [] # NOTE: rename this variable, as it no longer holds the title id
    dvd_title = user_config['dvd_title']
    special_feature = user_config['special_feature']
    tv_show_info = user_config['tv_show']

    media_info = {}
    iso_name = ''

    # NOTE: Maybe make a 'tv-show' function. This means you could pass special features as  {'season': 0, 'first_episode': 0, 'num_episodes': 0}
    # NOTE: This would clean up this messy if statement handling, as it checks for special features twice
    # Handles DVDs with multiple episodes
    if tv_show_info:
        # Get the media info from TMDB
        media_info = tmdb_tv_info(dvd_title)

        # Special features should be treated as Season 0, due to how plex and jellyfin handle special features
        season_number = 0 if special_feature else tv_show_info['season_number']
        # Adds a leading zero to the season and episode numbers for formatting (both Plex and Jellyfin use this format)
        formatted_season = f"{season_number:02d}"

        # Special features, need to be handle here, so it can be added as 'Season 0', within the TV folder structure
        # This is how both plex and Jellyfin handle special features
        # Setting the 'first_episode' and 'num_episode' to 0, prevents the for loop below from entering
        if not special_feature:
            first_episode = tv_show_info['first_episode']
            num_episodes = tv_show_info['num_episodes']

            # 1 is subtracted, is because the 'first episode' is included in the count
            iso_name = f"{dvd_title} s{formatted_season}e{first_episode:02d} - e{((first_episode+num_episodes)-1):02d}"

            # Get the runtime and episode name for each episode on the disc
            for episode_number in range(first_episode, first_episode + num_episodes):
                # Need to subtract 1 to episode_number as the list is 0-indexed
                episode_info = media_info['seasons'][season_number-1]['episodes'][episode_number-1] if media_info is not None else {'runtime': -1, 'name': f'Episode {episode_number-1}'}
                formatted_episode = f"{episode_number:02d}"
                titles_to_rip.append(
                    {
                        'file_name': f"{dvd_title} - s{formatted_season}e{formatted_episode} - {episode_info['episode_name']}",
                        'expected_runtime': episode_info['runtime']
                    }
                )

        # Create the path for the tv show and seasons, based on the file structure provided by Plex and Jellyfin
        season_folder_name = f"Season {formatted_season}"

        # NOTE: Maybe have the dict as a user input and if one is missing, assume that it does not need to create the file for that
        # NOTE: For iso, if it is not present, just point it to the dvd drive directly
        out_folders['mkv'] = Path(out_folders['mkv']) / 'TV Shows'
        for key in out_folders:
            out_folders[key] = Path(out_folders[key]) / dvd_title / season_folder_name
            out_folders[key].mkdir(parents=True, exist_ok=True)
    elif special_feature:
        # Special handling needs to be had if it is special features for a movie and not a TV show
        for key in out_folders:
            out_folders[key] = Path(out_folders[key]) / '' / f"{dvd_title} Special Features"
            out_folders[key].mkdir(parents=True, exist_ok=True)
    else:
        out_folders['mkv'] = Path(out_folders['mkv']) / 'Movies'
        media_info = tmdb_movie_info(dvd_title, tmdb_api_key=os.getenv('TMDB_API_KEY'))
        iso_name = dvd_title
        titles_to_rip.append(
            {
                'file_name': dvd_title,
                'expected_runtime': media_info['runtime'] if media_info is not None else -1
            }
        )

    if special_feature:
        iso_name = f"{dvd_title} Special Features"

    # TODO See a better way, as this check is performed in 'makemkv.disc_backup'. The option could just be removed as everywhere else performs the check anyways
    iso_filename = Path(out_folders['iso']) / f"{iso_name}.iso"

    handbrake = Handbrake(Path("C:\\Program Files\\HandBrake\\HandBrakeCLI.exe"), out_folders['mp4'])
    makemkv = MakeMKV(Path("C:\\Program Files (x86)\\MakeMKV\\makemkvcon"), out_folders['mkv'], out_folders['iso'])

    video_rip_apps: List[RipApps] = [
        RipApps(name="MakeMKV", app=makemkv, title_info=[]),
        RipApps(name="Handbrake", app=handbrake, title_info=[])
    ]

    encode = 'n' # Default to not encoding, if the user does not want to encode, then it will not start the decryption
    if not os.path.exists(iso_filename):
        encode = 'y'
        iso_filename = makemkv.disc_backup(iso_name)
        if iso_filename is None:
            print("Failed to create ISO image, aborting process.")
            return
        print('-' * 20)
        print('ISO Completed')
        print('-' * 20)
    else:
        print('Image already exists')
        encode = str(input('Proceed with encoding y/n: '))
        print('\nProcessing encoding, using existing ISO file.')

    if encode == 'y':
        for video_rip_app in video_rip_apps:
            video_rip_app.title_info = video_rip_app.app.extract_disc_title_info(iso_filename)

        print('-' * 20)
        print(titles_to_rip)
        print('-' * 20)

        for title in titles_to_rip:
            runtime = title['expected_runtime']
            filename = title['file_name']
            
            active_threads = []
            for video_rip_app in video_rip_apps:
                title_to_rip = video_rip_app.app.get_main_feature(video_rip_app.title_info, runtime)
                if title_to_rip >= 0:
                    new_thread = threading.Thread(
                        target=video_rip_app.app.extract_video,
                        args=(iso_filename, title_to_rip, filename)
                    )
                    new_thread.start()
                    active_threads.append(new_thread)
                else:
                    print("Invalid title ID, skipping encoding")
            
            for active_thread in active_threads:
                active_thread.join()

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

    user_input = console_user_input()

    while True:
        if dvd_detected(disc_drive):
            main(output_folders, user_input)