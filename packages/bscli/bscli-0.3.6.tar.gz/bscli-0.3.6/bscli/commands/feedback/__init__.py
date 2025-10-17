import argparse
from pathlib import Path
from bscli.commands.feedback import upload
from bscli.commands.base import BaseCommand, BaseGroupCommand


class UploadCommand(BaseCommand):
    """Upload graded feedback."""

    name = "upload"
    help = "Upload graded feedback"

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "submissions_path",
            type=Path,
            nargs="?",
            default=Path.cwd(),
            help="Path to submissions directory",
        )
        parser.add_argument(
            "--draft", action="store_true", help="Upload as draft feedback"
        )
        parser.add_argument(
            "--force", action="store_true", help="Overwrite existing feedback"
        )
        # Allow a "dry run" to walk through the upload process.
        # It will not make any actual changes (call APIs to change feedback/grades, upload files).
        # This is useful during development and testing to not upload incorrect feedback to Brightspace.
        parser.add_argument(
            "--dry-run", action="store_true", help="Do not upload feedback"
        )

    def execute(self, ctx, args: argparse.Namespace) -> None:
        upload.handle(ctx, args)


class FeedbackCommand(BaseGroupCommand):
    """Feedback management commands."""

    name = "feedback"
    help = "📤 Feedback management"

    def __init__(self):
        self.subcommands = {UploadCommand.name: UploadCommand}
