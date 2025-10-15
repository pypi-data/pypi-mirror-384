"""Tools to create a valid workflow zip archive from workflow.json file."""

import json
import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path, PureWindowsPath
from typing import BinaryIO

from yarl import URL

import ikcli.utils.path

logger = logging.getLogger(__name__)


class Archive:
    """Manager archive to send to ikomia service to deploy a workflow."""

    def __init__(self, filename: Path):
        """
        Initialize a new Archive.

        Args:
            filename: workflow filename to process
        """
        with open(filename, "rt", encoding="utf-8") as fh:
            self.workflow = json.load(fh)

        self.temporary_directory = None

    def prepare(self) -> BinaryIO:
        """
        Prepare zip archive to send to service.

        Returns:
            A zip file name
        """
        # Sanity check
        assert self.temporary_directory is None

        # Create temporary directory
        self.temporary_directory = tempfile.TemporaryDirectory(prefix="ikcli-workflow-")  # pylint: disable=R1732

        # Create temporary working directory
        directory = Path(self.temporary_directory.name)
        working_directory = directory / "workdir"
        working_directory.mkdir()

        # Add plugins
        self._add_plugins(working_directory)

        # Create workflow file
        with open(working_directory / "workflow.json", "wt", encoding="utf-8") as fh:
            json.dump(self.workflow, fh)

        # Zip working directory
        zip_filename = directory / "archive.zip"
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(working_directory):
                for filename in files:
                    filepath = Path(root, filename)
                    zipf.write(filepath, filepath.relative_to(working_directory))

        # Return zip file name
        return zip_filename

    def __enter__(self):
        """
        When used with ContextManager, prepare zip to send to service.

        Returns:
            A zip file handler
        """
        return self.prepare()

    def cleanup(self):
        """Clean temporary working files and directories."""
        # Sanity check
        assert self.temporary_directory is not None

        # Clean temporary directory
        self.temporary_directory.cleanup()
        self.temporary_directory = None

    def __exit__(self, *exc):
        """
        Cleanup when exit to ContextManager.

        Args:
            *exc: Information related to stack trace
        """
        self.cleanup()

    def _add_plugins(self, directory: Path):
        """
        Parse task list and embed plugins if needed.

        Args:
            directory: Directory to copy plugins

        Raises:
            ValueError: when plugin URL is not supported
        """
        logger.debug("Check to embedded plugins")

        # For each task, check if we have to embed plugin
        for task in self.workflow["tasks"]:
            data = task["task_data"]

            # Check if URL in data
            if "url" not in data:
                logger.debug("Task %s plugin is internal", data["name"])
                continue

            # Extract URL
            try:
                url = URL(task["task_data"]["url"])
            except ValueError:
                if not task["task_data"]["url"].startswith("file://"):
                    raise
                # There's a known issue with windows + ikomia<0.10.0 that mix '\\' and '/' on file url
                # eg : 'file://C:\\Users\\allan\\Ikomia/Plugins/Python/infer_neural_style_transfer'
                # So try to use pathlib to re-normalize path before giving to yarl
                normalized_path = PureWindowsPath(task["task_data"]["url"][7:])
                url = URL(normalized_path.as_uri())

            logger.debug("Task %s plugin is located at %s", data["name"], url)

            if url.scheme == "file":
                # If URL is file scheme, copy
                path = ikcli.utils.path.from_uri(url)
                dst = directory / data["name"]

                # Use Path.from_uri when python>3.13

                if os.path.exists(dst):
                    logger.debug("Destination plugin '%s' already exists.", dst)
                else:
                    logger.debug("Copy plugin from '%s' to '%s'", path, dst)
                    shutil.copytree(
                        format(path), dst, ignore=shutil.ignore_patterns(".git", ".github", ".gitignore", ".idea")
                    )

                # Copy local files inside plugin folder if necessary (models)
                self._add_local_files(path, data, directory)

                # Update url
                data["url"] = "file://" + data["name"]
            else:
                raise ValueError(f"Plugin url scheme '{url}' is not supported yet")

    def _add_local_files(self, src_plugin_path: Path, task_data: dict, directory: Path):
        """
        Parse parameters and embed local files (like models) if needed.

        Path parameters are then changed as relative path to algorithm folder.

        Args:
            src_plugin_path: Source plugin path
            task_data: Task data
            directory: Directory to copy files
        """
        # Craft data path
        data_path = directory / task_data["name"] / "data"

        for param in task_data["parameters"]:
            # Parse param value as PurePath and check if exists
            p = Path(param["value"])
            if not p.is_file():
                continue

            # Check if data file is already embed on plugin sources
            try:
                # Use Path.is_relative_to() instead of try/except when >=3.9
                p.relative_to(src_plugin_path)

                # Update param value as relative path
                param["value"] = f"file://{p.relative_to(src_plugin_path.parent)}"

            except ValueError:
                # Ensure data path exists
                data_path.mkdir(parents=True, exist_ok=True)

                # Copy file
                dst = data_path / p.name
                shutil.copy2(str(p), str(dst))  # Remove 'str' when >=3.8

                # Update param value as relative path
                param["value"] = f"file://{dst.relative_to(directory)}"
