import json
import logging
from pathlib import Path

from bsapi import APIConfig

from bscli.processing import GraderProcessing
from bscli.progress import ProgressReporter

logger = logging.getLogger(__name__)


class AddAPIConfig(GraderProcessing):
    def __init__(
        self,
        config: APIConfig,
        progress_reporter: ProgressReporter = None,
    ):
        super().__init__(progress_reporter)
        self.config = config

    def process_grader(self, grader_path: Path):
        config_path = grader_path / "data" / "bsapi.json"
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(self.config.to_json(), indent=4, ensure_ascii=False))
