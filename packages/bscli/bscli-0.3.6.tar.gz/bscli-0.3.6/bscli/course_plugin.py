from __future__ import annotations

from abc import ABC

from bscli.config import AssignmentConfig
from bscli.division import Divider
from bscli.processing import GraderProcessing, SubmissionsProcessing


class CoursePlugin(ABC):
    def __init__(self, name: str):
        self.name = name

    def initialize(self) -> bool:
        return True

    def get_divider(
        self, assignment_id: str, assignment_config: AssignmentConfig
    ) -> Divider:
        raise NotImplementedError

    def pre_extract_passes(
        self, assignment_id: str, assignment_config: AssignmentConfig
    ) -> list[SubmissionsProcessing]:
        """Submission passes to run before submission archives are extracted."""
        return []

    def pre_clean_passes(
        self, assignment_id: str, assignment_config: AssignmentConfig
    ) -> list[SubmissionsProcessing]:
        """Submission passes to run before extracted submission files are cleaned up."""
        return []

    def pre_hierarchy_passes(
        self, assignment_id: str, assignment_config: AssignmentConfig
    ) -> list[SubmissionsProcessing]:
        """Submission passes to run before applying file hierarchy modifications."""
        return []

    def pre_inject_passes(
        self, assignment_id: str, assignment_config: AssignmentConfig
    ) -> list[SubmissionsProcessing]:
        """Submission passes to run before injecting submission assignment files."""
        return []

    def pre_move_passes(
        self, assignment_id: str, assignment_config: AssignmentConfig
    ) -> list[SubmissionsProcessing]:
        """Submission passes to run before submission files are moved to grader folders."""
        return []

    def pre_grader_inject_passes(
        self, assignment_id: str, assignment_config: AssignmentConfig
    ) -> list[GraderProcessing]:
        """Grader passes to run before injecting grader assignment files."""
        return []

    def pre_grader_files_passes(
        self, assignment_id: str, assignment_config: AssignmentConfig
    ) -> list[GraderProcessing]:
        """Grader passes to run before adding grader files."""
        return []

    def pre_grader_archive_passes(
        self, assignment_id: str, assignment_config: AssignmentConfig
    ) -> list[GraderProcessing]:
        """Grader passes to run before creating grader archives."""
        return []

    def pre_grader_upload_passes(
        self, assignment_id: str, assignment_config: AssignmentConfig
    ) -> list[GraderProcessing]:
        """Grader passes to run before uploading grader archives."""
        return []


class DefaultCoursePlugin(CoursePlugin):
    def __init__(self):
        super().__init__("default")
