import logging
from datetime import datetime
from pathlib import Path
from typing import List
import json

from src.api import Api, WorkoutSummary
from src.exporters.base_exporter import BaseExporter, parse_points

LOGGER = logging.getLogger(__name__)


class Scraper:
    def __init__(
        self, api: Api, exporter: BaseExporter, output_dir: Path, file_format: str
    ):
        self.api: Api = api
        self.exporter: BaseExporter = exporter
        self.output_dir: Path = output_dir
        self.file_format: str = file_format

    def get_output_file_path(self, file_name: str) -> Path:
        return (self.output_dir / file_name).with_suffix(f".{self.file_format}")

    def fetch_workout_summaries(self) -> List[WorkoutSummary]:
        summaries: List[WorkoutSummary] = []

        history = self.api.get_workout_history()
        summaries.extend(history.data.summary)

        while history.data.next != -1:
            logging.info(
                f"Fetching more summaries starting from workout {history.data.next}"
            )
            history = self.api.get_workout_history(from_track_id=history.data.next)
            summaries.extend(history.data.summary)

        logging.info(f"There are {len(summaries)} workouts in total")
        return summaries

    def workout_summary_to_dict(self,summary):
        pause_time = None
        if summary.pause_time:
            if int(summary.pause_time) > 0:
                pause_time = datetime.fromtimestamp(int(summary.pause_time)).strftime("%M:%S")

        return {
            'date': datetime.fromtimestamp(int(summary.trackid)).strftime("%Y-%m-%d"),
            'start_time': datetime.fromtimestamp(int(summary.trackid)).strftime("%H:%M:%S"),
            'end_time': datetime.fromtimestamp(int(summary.end_time)).strftime("%H:%M:%S"),
            'run_time': datetime.fromtimestamp(int(summary.run_time)).strftime("%H:%M:%S"),
            'calorie': summary.calorie,
            'avg_heart_rate': summary.avg_heart_rate,
            'type': summary.type,
            'max_heart_rate': summary.max_heart_rate,
            'min_heart_rate': summary.min_heart_rate,
            'pause_time': pause_time
        }
    def run(self) -> None:
        summaries = self.fetch_workout_summaries()
        self.output_dir.mkdir(exist_ok=True)

        for summary in summaries:
            detail = self.api.get_workout_detail(summary)
            file_name = datetime.fromtimestamp(int(summary.trackid)).strftime("Workout--%Y-%m-%d--%H-%M-%S")
            output_file_path = self.get_output_file_path(file_name)

            try:
                with open(output_file_path, 'w') as f:
                    json.dump(self.workout_summary_to_dict(summary), f)

                LOGGER.info(f"Successfully saved {output_file_path}")
            except Exception as e:
                LOGGER.error(f"Failed to save {output_file_path}: {e}")
