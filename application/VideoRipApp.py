from pydantic import BaseModel
from typing import List
import os
from abc import ABC, abstractmethod
from pathlib import Path

class TitleInfo(BaseModel):
    title_id: int
    runtime: int

class SeasonInformation(BaseModel):
    runtime: int
    info: str = ""

class VideoRipApp(ABC):
    def __init__(self, application_path: Path, file_extension: str, out_path: Path):
        self.application_path = application_path
        self.file_extension = file_extension
        self.out_path = out_path

    @property
    def application_path(self) -> Path: return self._application_path
    
    @application_path.setter
    def application_path(self, path: Path):
        if not os.path.exists(path):
            # TODO Find out why this causes an error with makemkv
            print('Application Path not Valid')
            # raise FileNotFoundError(f"Application path does not exist: {path}")
        self._application_path = path

    @property
    def file_extension(self) -> str: return self._file_extension
    
    @file_extension.setter
    def file_extension(self, extension: str):
        if not extension.startswith('.'):
            raise ValueError(f"File extension must start with a '.': {extension}")
        self._file_extension = extension

    @property
    def out_path(self) -> Path: return self._out_path
    
    @out_path.setter
    def out_path(self, path: Path):
        if not os.path.exists(path):
            print(f"Path does not exist: {path}")
            print(f"Creating directory: {path}")
            os.makedirs(path)
            print(f"Directory created: {path}")
        self._out_path = path

    @property
    @staticmethod
    def special_feature_runtime_threshold() -> int: return 5
    
    @abstractmethod
    def _extract_video_file(self, iso_filename: str, title_id: int, output_path: str) -> str:
        return ''

    @staticmethod
    @abstractmethod
    def _raw_title_info(self, iso_filename: str) -> dict: return {}

    @staticmethod
    @abstractmethod
    def _parse_raw_title_info(self, raw_title_info: List) -> List[TitleInfo]: return []

    def special_feature_titles(self, title_data: List[TitleInfo], special_features_info: List[SeasonInformation]) -> List[int]:
        all_titles = []
        previous_title_ids = []
        previous_title_episodes = [] # Used to prevent the same episode being used for multiple titles

        for title in title_data:
            title_id = title['title_id']
            runtime = title['runtime']
            filename = f"Title {title_id}"
            
            # Check if this title matches any special feature
            for feature in special_features_info:
                expected_runtime = feature['runtime']
                runtime_threshold = self.special_feature_runtime_threshold()
                
                if runtime >= (expected_runtime - runtime_threshold) and runtime <= (expected_runtime + runtime_threshold) and title_id not in previous_title_ids and feature['episode_number'] not in previous_title_episodes:
                    previous_title_episodes.append(feature['episode_number'])
                    filename = feature['episode_name']
                    break

            previous_title_ids.append(title_id)
            all_titles.append({
                'title_id': title_id,
                'file_name': filename
            })
            
        return all_titles
    
    def extract_video(self, iso_filename: str, title_id: int, file_name: str) -> str:
        if not os.path.exists(iso_filename):
            raise FileNotFoundError(f"ISO file does not exist: {iso_filename}")

        output_filename = os.path.join(self.out_path, f"{file_name}{self.file_extension}")
        if os.path.exists(output_filename):
            print(f"Output file already exists, skipping extraction: {output_filename}")
            return output_filename
        return self._extract_video_file(iso_filename, title_id, output_filename)

    def extract_disc_title_info(self, iso_filename: str) -> List[TitleInfo]:
        raw_title_info = self._raw_title_info(iso_filename)
        title_info = self._parse_raw_title_info(raw_title_info)
        return title_info

    def get_main_feature(self, title_data: List[TitleInfo], expected_runtime: int, runtime_threshold: int=10, previous_title_ids: List[int]=[]) -> int:
        highest_runtime = -1
        backup_title_id = -1

        for title in title_data:
            title_id = title.title_id
            runtime = title.runtime

            # Check if this title matches the expected runtime
            if runtime >= (expected_runtime - runtime_threshold) and runtime <= (expected_runtime + runtime_threshold) and title_id not in previous_title_ids:
                print(f"Found matching runtime title: {title_id}, runtime: {runtime} minutes")
                return title_id
            elif runtime > highest_runtime:
                highest_runtime = runtime
                backup_title_id = title_id

        # Fall back to the title with the highest runtime
        if highest_runtime > 0:
            print(f"No exact match found, using highest runtime title: {backup_title_id}, runtime: {highest_runtime} minutes")
            return backup_title_id

        print("No matching title found.")
        return -1