"""Manage local algo ( ie bare code on local machine )."""

# 'E1101: no-member' is disabled because of problem with python binding resolution
#   => E1101: Module 'ikomia.utils' has no 'ApiLanguage' member (no-member)
# pylint: disable=E1101

import enum
import logging
import os.path
import platform
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Generator, List

from cookiecutter.main import cookiecutter
from ikomia.core import config
from ikomia.dataprocess.registry import ik_registry
from ikomia.utils import ApiLanguage, OSType, algorithm

logger = logging.getLogger(__name__)


@enum.unique
class ProgrammingLanguages(enum.IntEnum):
    """Package programming language enum use by ikomia lib."""

    CPP = 0
    PYTHON = 1


@enum.unique
class AlgoTypes(enum.IntEnum):
    """Algo general types enum used by Ikomia lib."""

    INFER = 0
    TRAIN = 1
    DATASET = 2
    OTHER = 3


class Algo:
    """Interface between ikomia lib and ikomia scale to manage algos."""

    def __init__(self, name: str):
        """
        Initialize a new algo object.

        Args:
            name: Algo name

        Raises:
            ValueError: when algo doesn't exist on local machine
            TypeError: when trying to process internal algo
        """
        # Ensure algorithm name is a valid local plugin, raise or return None otherwise
        ik_algo = ik_registry.create_algorithm(name=name, public_hub=False, private_hub=False)
        if ik_algo is None:
            raise ValueError(f"Local algo '{name}' not found.")

        # This function may return a None or throw exception if algo doesn't exist,
        #  but it doesn't. Check name is not empty to ensure algo exists.
        info = ik_registry.get_algorithm_info(name)
        if len(info.name) == 0:
            raise ValueError(f"Local algo '{name}' not found.")

        # Check if algo is internal or not
        if info.internal:
            raise TypeError("Can't process internal algo '{name}'.")

        self.name = name
        self._info = info
        self._path = None
        self.tmp_workflow_file = None

    def __getitem__(self, key):
        """
        Return algo information, dict fashion.

        Args:
            key: algo info key

        Returns:
            Algo info value
        """
        if key == "path":
            return self.path
        return getattr(self._info, key)

    @classmethod
    def list(cls) -> Generator[str, None, None]:
        """
        List non internal algos.

        Yields:
            Local algo name
        """
        # Manage lazy loading and load all algorithms if necessary
        lazy_load = config.main_cfg["registry"].get("lazy_load", True)
        if lazy_load and not ik_registry.is_all_loaded():
            ik_registry.load_algorithms()

        for name in ik_registry.get_algorithms():
            info = ik_registry.get_algorithm_info(name)
            if not info.internal:
                yield name

    @classmethod
    def create(
        cls,
        name: str,
        base_class: str = "CWorkflowTask",
        widget_class: str = "CWorkflowTaskWidget",
        qt_framework: str = "pyqt",
    ) -> "Algo":
        """
        Create a new empty python algo code.

        Args:
            name: New algo name
            base_class: Class new algo inherits
            widget_class: Class new widget class inherits
            qt_framework: QT framework to use. Can be pyqt or pyside

        Returns:
            New algo

        Raises:
            ValueError: when algo name is not valid
        """
        # Try to load algo name. Raise exception if exists.
        ik_algo = None
        try:
            ik_algo = ik_registry.create_algorithm(name=name, public_hub=False, private_hub=False)
        except Exception:  # pylint: disable=W0718
            pass

        if ik_algo is not None:
            raise ValueError(f"Local algo '{name}' already exists.")

        # Enforce check with plugin directory
        python_plugin_directory = Path(ik_registry.get_plugins_directory(), "Python")
        if (python_plugin_directory / name).exists():
            raise ValueError(f"Plugin '{name}' already exists in {python_plugin_directory}")

        # Craft valid algo name and class
        algo_name = re.sub(r"\s+", "", name, flags=re.UNICODE).lower()
        if not algo_name.isidentifier():
            raise ValueError(f"'{name}' is not a valid algo name as '{algo_name}' is not a valid module name")
        algo_class_name = re.sub(r"(_|-)+", " ", name).title().replace(" ", "")
        if not algo_class_name.isidentifier():
            raise ValueError(f"'{name}' is not a valid algo name as '{algo_class_name}' is not a valid class name")

        # Craft context
        context = {
            "plugin_dir": name,
            "algo_name": algo_name,
            "class_name": algo_class_name,
            "base_class": base_class,
            "widget_class": widget_class,
            "qt_framework": qt_framework,
        }

        # Generate algo template using cookiecutter
        template_path = Path(__file__).parent / "templates"
        cookiecutter(
            format(template_path),
            extra_context=context,
            no_input=True,
            overwrite_if_exists=False,
            output_dir=format(python_plugin_directory),
        )

        # Check loading of the newly created algorithm
        ik_algo = ik_registry.create_algorithm(name=name, public_hub=False, private_hub=False)
        if ik_algo is None:
            raise ValueError(f"Creation of local algo '{name}' failed.")

        # Return algo
        return cls(name)

    @property
    def path(self) -> Path:
        """
        Return local algo path.

        Returns:
            algo path

        Raises:
            TypeError: when algo language is not supported.
            FileNotFoundError: when algo path doesn't exist.
        """
        if self._path is None:
            # Craft path by algo language
            if self._info.language == ApiLanguage.CPP:
                self._path = Path(ik_registry.get_plugins_directory(), "C++", self.name)
            elif self._info.language == ApiLanguage.PYTHON:
                self._path = Path(ik_registry.get_plugins_directory(), "Python", self.name)
            else:
                raise TypeError(f"Don't support {self._info.language} language for algo")

            # Sanity check
            if not self._path.exists():
                raise FileNotFoundError(f"Algo '{self.name}' path '{self._path}' doesn't exists")
        return self._path

    @property
    def info(self) -> dict:
        """
        Return structured data about local algo.

        This intends to be use by ikomia scale api object.

        Returns:
            A dict with algo info usable by ikomia scale algo object.
        """
        # Extract main data
        data = {
            "name": self._info.name,
            "short_description": self._info.short_description,
            "description": self._info.description,
            "keywords": [kw.strip() for kw in self._info.keywords.split(",")],
            "paper": {
                "authors": self._info.authors,
                "title": self._info.article,
                "journal": self._info.journal,
                "year": self._info.year,
                "link": self._info.article_url,
            },
            "ikomia_min_version": self._info.min_ikomia_version,
            "ikomia_max_version": self._info.max_ikomia_version,
            "python_min_version": self._info.min_python_version,
            "python_max_version": self._info.max_python_version,
            "language": ProgrammingLanguages(self._info.language).name,
            "repository": self._info.repository,
            "original_implementation_repository": self._info.original_repository,
            "algo_type": AlgoTypes(self._info.algo_type).name,
            "algo_task": [algo_task.strip().upper() for algo_task in self._info.algo_tasks.split(",")],
            "os": self._get_compatible_os_list(),
        }

        # If a README.MD exists, override description with content
        for f in self.path.iterdir():
            if f.name.upper() == "README.MD":
                with f.open("r") as readme:
                    data["description"] = readme.read()

        # Add icon path if defined
        if self._info.icon_path is None or len(self._info.icon_path) == 0:
            data["icon"] = None
        else:
            data["icon"] = self.path / self._info.icon_path

        return data

    def _get_compatible_os_list(self) -> List[str]:
        """
        Get OS list from Ikomia API enum.

        Returns:
            list(str): list of compatible operating systems.
        """
        if self._info.os == OSType.ALL:
            return ["LINUX", "WINDOWS"]
        if self._info.os == OSType.WIN:
            return ["WINDOWS"]
        if self._info.os == OSType.LINUX:
            return ["LINUX"]
        return []

    def create_workflow(self) -> str:
        """
        Create demo workflow for the given algorithm.

        Returns:
            workflow path (str)
        """
        wf = algorithm.create_demo_workflow(self.name)
        self.tmp_workflow_file = tempfile.NamedTemporaryFile(suffix=".json")  # pylint: disable=R1732
        wf.save(self.tmp_workflow_file.name)
        return self.tmp_workflow_file.name


class Package:
    """Package local code to send to ikomia scale."""

    def __init__(self, algo: Algo):
        """
        Initialize a new algo package.

        Args:
            algo: Algo to package
        """
        self.algo = algo
        self.temporary_directory = None

    def prepare(self):
        """
        Prepare zip package to send to service.

        Returns:
            A zip file handler
        """
        # Sanity check
        assert self.temporary_directory is None

        # Create temporary directory
        self.temporary_directory = tempfile.TemporaryDirectory(prefix="ikcli-algo-")  # pylint: disable=R1732

        # Create temporary working directory
        directory = Path(self.temporary_directory.name)
        working_directory = directory / self.algo.name

        # Copy algo code avoiding working files
        def _algo_copy_ignore_files(_, filenames: List[str]) -> List[str]:
            """
            Return a list of files to ignore when copy algo local code.

            Args:
                filenames: File names present in path

            Returns:
                A list of files to ignore
            """
            filenames_to_ignore = ["__pycache__", ".git", ".vscode", ".idea"]
            return [filename for filename in filenames if filename in filenames_to_ignore]

        shutil.copytree(self.algo.path, working_directory, ignore=_algo_copy_ignore_files)

        # Zip working directory
        zip_filename = directory / "package.zip"
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(working_directory):
                for filename in files:
                    filepath = Path(root, filename)
                    zipf.write(filepath, filepath.relative_to(working_directory))

        # Return zip file name
        return zip_filename

    def cleanup(self):
        """Clean temporary working files and directories."""
        # Sanity check
        assert self.temporary_directory is not None

        # Clean temporary directory
        self.temporary_directory.cleanup()
        self.temporary_directory = None
        pass

    def __enter__(self):
        """
        When used with ContextManager, prepare zip to send to service.

        Returns:
            A zip file handler
        """
        return self.prepare()

    def __exit__(self, *exc):
        """
        Cleanup when exit to ContextManager.

        Args:
            *exc: Information related to stack trace
        """
        self.cleanup()


def get_platform_information() -> dict:
    """
    Return a set of information about local platform needed to upload package.

    Returns:
        A set of local platform information
    """
    return {
        "python_version": get_local_python_version(),
        "os": [platform.system().upper()],  # 'LINUX', 'DARWIN', 'JAVA', 'WINDOWS'
        "architecture": [platform.machine().upper()],  # X86_64, ARM64, I686
    }


def get_local_python_version() -> str:
    """
    Return Python version of the current environment.

    Returns:
        str: current Python version as major.minor string.
    """
    # Only give major + minor
    (major, minor, _) = platform.python_version_tuple()
    return (f"{major}.{minor}",)
