from pydantic import BaseModel
from typing import List
import os
from abc import ABC, abstractmethod

class TitleInfo(BaseModel):
    title_id: int
    runtime: int
    info: str = ""

class SeasonInformation(BaseModel):
    runtime: int
    info: str = ""


class VideoRipApp(ABC):
    def __init__(self, application_path: str):
        if not os.path.exists(application_path):
            raise FileNotFoundError(f"Application path does not exist: {application_path}")
        self.application_path = application_path
        pass

    @property
    def application_path() -> str:
        """Path to the application."""
        pass

    @abstractmethod
    def extract_disc_title_info(self, iso_filename: str) -> List[TitleInfo]:
        return []
    
    @abstractmethod
    def extract_subtitle_file(self, iso_filename: str, title_id: int, output_path: str) -> str:
        return ''
    
    @abstractmethod
    def extract_video_file(self, iso_filename: str, title_id: int, output_path: str) -> str:
        return ''

    @staticmethod
    def special_feature_titles(title_data: List[TitleInfo], special_features_info: List[SeasonInformation]) -> List[int]:
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
                runtime_threshold = 5  # Threshold in minutes
                
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

    @staticmethod
    def get_title_id(title_data: List[TitleInfo], expected_runtime: int, runtime_threshold: int=10, previous_title_ids: List[int]=[]) -> int:
        highest_runtime = -1
        backup_title_id = -1
        
        for title in title_data:
            title_id = title['title_id']
            runtime = title['runtime']
            
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