import logging
import subprocess
from pathlib import Path

from bscli.processing import SubmissionsProcessing
from bscli.processing.utils import get_all_files

logger = logging.getLogger(__name__)


class DocxToPdf(SubmissionsProcessing):
    def process_submission(self, submission_path: Path):
        for file in get_all_files(submission_path):
            if file.suffix.lower() == ".docx":
                args = [
                    "libreoffice",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    file.parent,
                    file,
                ]
                cp = subprocess.run(args, shell=False, check=False, capture_output=True)
                if cp.returncode != 0:
                    logger.warning(
                        'Converting "%s" to PDF failed: %s (exit code %d)',
                        file.name,
                        cp.stderr.decode("utf-8"),
                        cp.returncode,
                    )

    def execute(self, path: Path):
        # Check whether libreoffice is installed.
        args = ["libreoffice", "--version"]
        try:
            cp = subprocess.run(args, shell=False, check=False, capture_output=True)
            if cp.returncode == 0:
                logger.debug("Found LibreOffice version %s", cp.stdout.decode("utf-8"))
                super().execute(path)
            else:
                logger.warning(
                    "Skipping DOCX to PDF conversion as LibreOffice was not found"
                )
                print("\n⚠️  LibreOffice is not installed or not found in PATH")
                print("DOCX to PDF conversion will be skipped.")
                print(
                    "\n📄 To enable DOCX to PDF conversion, please install LibreOffice:"
                )
                print("\n  macOS:")
                print("    brew install --cask libreoffice")
                print("\n  Linux (Debian/Ubuntu):")
                print("    sudo apt-get install libreoffice")
                print("\n  Linux (Fedora/RHEL):")
                print("    sudo dnf install libreoffice")
                print("\n  Windows:")
                print("    Download from https://www.libreoffice.org/")
                print("    Or use: choco install libreoffice")
                print()
        except FileNotFoundError:
            logger.warning(
                "Skipping DOCX to PDF conversion as LibreOffice was not found"
            )
            print("\n⚠️  LibreOffice is not installed or not found in PATH")
            print("DOCX to PDF conversion will be skipped.")
            print("\n📄 To enable DOCX to PDF conversion, please install LibreOffice:")
            print("\n  macOS:")
            print("    brew install --cask libreoffice")
            print("\n  Linux (Debian/Ubuntu):")
            print("    sudo apt-get install libreoffice")
            print("\n  Linux (Fedora/RHEL):")
            print("    sudo dnf install libreoffice")
            print("\n  Windows:")
            print("    Download from https://www.libreoffice.org/")
            print("    Or use: choco install libreoffice")
            print()
