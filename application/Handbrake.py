import json
import subprocess
from application.VideoRipApp import VideoRipApp, TitleInfo
from typing import List
from pathlib import Path

class Handbrake(VideoRipApp):
    def __init__(self, application_path: Path, mp4_out_path: Path = "."):
        super().__init__(application_path, '.mp4', mp4_out_path)
        pass

    def _raw_title_info(self, iso_filename: str) -> dict:
        title_command = [
            self.application_path,
            "--scan",
            "--json",
            "-i", iso_filename,
            "-t", "0"  # List all titles
        ]

        try:
            print(f"Starting retrieving disc information using HandBrakeCLI...")
            disc_info = subprocess.run(title_command, check=True, text=True, capture_output=True)
            print(f"Information retrieval completed.")
            raw_output = disc_info.stdout
            raw_title_info = raw_output.split('JSON Title Set:')[1].strip()
            return json.loads(raw_title_info)
        except FileNotFoundError:
            print("Error: HandBrakeCLI not found. Please check the path to HandBrakeCLI.")
        except subprocess.CalledProcessError as e:
            print(f"Error: HandBrakeCLI failed with error code {e.returncode}.")

    def _parse_raw_title_info(self, raw_title_info: List) -> List[TitleInfo]:
        title_data = []
        for title in raw_title_info['TitleList']:
            title_id = title['Index']
            runtime = (title['Duration']['Hours'] * 60)  + title['Duration']['Minutes']
            title_data.append(TitleInfo(title_id=title_id, runtime=runtime))
        return title_data
        # return title_set['MainFeature'] # Fallback to main feature if no match found, which is the longest title
    
    def _extract_video_file(self, iso_filename: str, title_id: int, output_path: str) -> str:
        """
        Automatically starts HandBrake encoding with the preset 'Fast 1080p30'.

        :param input_file: Path to the input video file.
        :param output_file: Path to the output encoded video file.
        """

        # HandBrakeCLI command with the 'Fast 1080p30' preset
        # The preset does not upscale, this is an upper limit of quality
        command = [
            self.application_path,
            "-i", iso_filename,
            "-o", output_path,
            # "-f", f"av_{file_format}",
            "--preset", "Fast 1080p30"
        ]

        if title_id:
            command.extend(["--title", str(title_id)])

        try:
            # Run the HandBrakeCLI command
            print(f"Starting HandBrake encoding for {iso_filename}...")
            subprocess.run(command, check=True)
            print(f"Encoding completed. Output saved to {output_path}.")
        except FileNotFoundError:
            print("Error: HandBrakeCLI not found. Please check the path to HandBrakeCLI.")
        except subprocess.CalledProcessError as e:
            print(f"Error: HandBrakeCLI failed with error code {e.returncode}.")

if __name__ == "__main__":
    app = Handbrake("C:\\Program Files\\HandBrake\\HandBrakeCLI.exe", "F:\\test\\")
    print(app.application_path)

    disc_info = app.extract_disc_title_info("F:\\Movies\\21 Jump Street.iso")
    main_feature_title = app.get_main_feature(disc_info, 105)
    print(f"Main feature title ID: {main_feature_title}")

    app.extract_video("F:\\Movies\\21 Jump Street.iso", main_feature_title, "21 Jump Street")

