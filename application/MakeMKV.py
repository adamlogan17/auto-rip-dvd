from pathlib import Path
import subprocess
from application.VideoRipApp import VideoRipApp, TitleInfo
from typing import List
import os
import re

class MakeMKV(VideoRipApp):
    def __init__(self, application_path: Path, mkv_out_path: Path = Path("."), iso_out_path: Path = Path(".")):
        super().__init__(application_path, '.mkv', mkv_out_path)
        self.iso_out_path = iso_out_path
        pass

    @property
    def iso_out_path(self) -> Path: return self._iso_out_path
    
    @iso_out_path.setter
    def iso_out_path(self, path: Path):
        if not os.path.exists(path):
            print(f"Path does not exist: {path}")
            print(f"Creating directory: {path}")
            os.makedirs(path)
            print(f"Directory created: {path}")
        self._iso_out_path = path

    def disc_backup(self, disc_name: str) -> Path | None:
        disc_number = 0
        
        output = Path(self.iso_out_path / f"{disc_name}.iso")
        
        if os.path.exists(output):
            print(f"Output file already exists, skipping extraction: {output}")
            return output

        rip_command = [
            self.application_path,
            'backup',
            f"disc:{disc_number}", # is whatever is in the disc drive (may need to change index, if multiple drive). Possible solution is to use the 'file:<>' option and point to 'E:'
            output,
            '--noscan',
            '--decrypt'
        ]

        try:
            print(f"Starting MakeMKV decryption for disc:{disc_number}...")
            subprocess.run(rip_command, check=True)
            print(f"Decryption completed. Output saved to {output}.")
            return output
        except FileNotFoundError:
            print("Error: MakeMKV not found. Please check the path to MakeMKV.")
            return None
        except subprocess.CalledProcessError as e:
            print(f"Error: MakeMKV failed with error code {e.returncode}.")
            return None

    def _raw_title_info(self, iso_filename: Path) -> str | None:
        info_command = [
            self.application_path,
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
            return None
        except subprocess.CalledProcessError as e:
            print(f"Error: MakeMKV failed with error code {e.returncode}.")
            return None

    def _parse_raw_title_info(self, raw_title_info: str) -> List[TitleInfo]:
        title_data: List[TitleInfo] = []
        
        for line in raw_title_info.splitlines():
            processed_line = line.split(',')
            info_title = processed_line[0].split(':')
            info_type = info_title[0]
            
            if 'TINFO' in info_type:
                title_id = int(info_title[1])
                info = processed_line[-1].strip('"')
                runtime = -1
                
                # Check if the info is a runtime in the format HH:MM or HH:MM:SS
                if re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', info):
                    time_parts = info.split(':')
                    if len(time_parts) == 3:
                        hours = int(time_parts[0])
                        minutes = int(time_parts[1])
                        runtime = (hours * 60) + minutes
                    elif len(time_parts) == 2:
                        hours = int(time_parts[0])
                        minutes = int(time_parts[1])
                        runtime = (hours * 60) + minutes
                
                # Only add entries with valid runtime data
                if runtime > 0:
                    title_data.append(TitleInfo(title_id=title_id, runtime=runtime))
        return title_data
            
    def _extract_video_file(self, iso_filename: Path, title_id: int, output_path: Path) -> Path | None:
        output = os.path.dirname(output_path)
        current_files = os.listdir(output)
        file_name = os.path.basename(output_path)

        mkv_command = [
            self.application_path,
            'mkv',
            f"file:{iso_filename}",
            f"{title_id}",
            output,
            '--noscan'
        ]
        
        try:
            print(f"Starting MakeMKV decryption for disc:0...")
            subprocess.run(mkv_command, check=True)
            print(f"Decryption completed. Output saved to {output}.")
        except FileNotFoundError:
            print("Error: MakeMKV not found. Please check the path to MakeMKV.")
            return None
        except subprocess.CalledProcessError as e:
            print(f"Error: MakeMKV failed with error code {e.returncode}.")
            return None

        updated_files = os.listdir(output)
        new_file_name = list(set(updated_files) - set(current_files))
        if new_file_name:
            new_file_path = os.path.join(output, new_file_name[0])
            mkv_name = os.path.join(output, file_name)
            os.rename(new_file_path, mkv_name)

if __name__ == "__main__":
    app = MakeMKV(Path("C:\\Program Files (x86)\\MakeMKV\\makemkvcon"), Path("F:\\test"), Path("F:\\test"))
    print(app.application_path)

    iso_file = app.disc_backup("A Few Good Men")
    if iso_file is not None:
        disc_info = app.extract_disc_title_info(iso_file)
        main_feature_title = app.get_main_feature(disc_info, 138)
        print(f"Main feature title ID: {main_feature_title}")

        app.extract_video(iso_file, main_feature_title, "A Few Good Men")

