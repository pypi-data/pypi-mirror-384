"""Parse and manipulate version."""

import re


class Version:
    """A version object to manage, validate or compare versions."""

    def __init__(self, version: str):
        """
        Initialize a new version.

        Args:
            version: Version as str
        """
        p_version = self.__class__._parse(version)

        self.major = p_version["major"]
        self.minor = p_version["minor"]
        self.patch = p_version["patch"]
        self.release = p_version["release"]
        self.metadata = p_version["metadata"]

    def __hash__(self) -> int:
        """
        Hash Version object to use it as dict key.

        Returns:
            A hash of version object
        """
        return hash((self.major, self.minor, self.patch, self.release, self.metadata))

    def __repr__(self) -> str:
        """
        Return a human readable representation of version.

        Returns:
            A str to represent version
        """
        v = f"{self.major}.{self.minor}"
        if self.patch is not None:
            v += f".{self.patch}"
        if self.release is not None:
            v += f"-{self.release}"
        if self.metadata is not None:
            v += f"+{self.metadata}"
        return v

    @classmethod
    def _parse(cls, version: str) -> dict:
        """
        Parse version and return dict for each version member (ie major / minor / patch / release and metadata).

        Args:
            version: Version to parse

        Returns:
            A dict that contains an entry for each version member

        Raises:
            ValueError: If version is not semver compatible
        """
        m = re.match(
            r"^(?P<major>\d+)\.(?P<minor>\d+)(\.(?P<patch>\d+))?"
            r"(-(?P<release>[0-9a-zA-Z-\.]+))?(\+(?P<metadata>[0-9a-zA-Z-\.]+))?$",
            version,
        )
        if m is None:
            raise ValueError(f"'{version}' is not a valid version")
        groupdict = m.groupdict()
        return {
            "major": int(groupdict["major"]),
            "minor": int(groupdict["minor"]),
            "patch": None if groupdict["patch"] is None else int(groupdict["patch"]),
            "release": groupdict["release"],
            "metadata": groupdict["metadata"],
        }

    def _cmp(self, other) -> int:  # pylint: disable=R0911
        """
        Compare two versions.

        Args:
            other: An other version

        Returns:
            A int as result. 0 is equals, <0 if other is greater, >0 if other is less.

        Raises:
            TypeError: If other is not a version object
        """
        if not isinstance(other, self.__class__):
            raise TypeError(f"Can't compare version and {other.__class__}")

        # Compare major
        if self.major > other.major:
            return 1
        if self.major < other.major:
            return -1

        # Compare minor
        if self.minor > other.minor:
            return 1
        if self.minor < other.minor:
            return -1

        # Special case : patch to None is same than 0
        sp = 0 if self.patch is None else self.patch
        op = 0 if other.patch is None else other.patch

        if sp > op:
            return 1
        if sp < op:
            return -1

        # Compare release. If they are None, versions are equals
        if self.release is None and other.release is None:
            return 0

        # If one has no release but the other has, it's greater
        if self.release is None:
            return 1
        if other.release is None:
            return -1

        # Both have release.
        # Use a simple alpha order to know which one is greater
        # It's not fully semver compatible,
        # but really simpler and functional most of the time.
        if self.release > other.release:
            return 1
        return -1

    def clone(self, major: int = None, minor: int = None, patch: int = None) -> "Version":
        """
        Return a new version that can be overriden by args.

        Args:
            major: A major digit for version. If None use this version major.
            minor: A minor digit for version. If None use this version minor.
            patch: A patch digit for version. If None use this version patch.

        Returns:
            A new Version
        """
        major = self.major if major is None else major
        minor = self.minor if minor is None else minor
        patch = self.patch if patch is None else patch

        if patch is None:
            return self.__class__(f"{major}.{minor}")
        return self.__class__(f"{major}.{minor}.{patch}")

    def next_major(self) -> "Version":
        """
        Return next major version.

        Returns:
            Next major Version
        """
        patch = self.patch if self.patch is not None else 0

        # Check if pre-major release
        if self.minor == 0 and patch == 0 and self.release is not None:
            return self.clone(patch=0)

        # Otherwise increment major and return version with minor and patch to zero
        major = self.major + 1
        return self.clone(major=major, minor=0, patch=0)

    def next_minor(self) -> "Version":
        """
        Return next minor version.

        Returns:
            Next minor version.
        """
        patch = self.patch if self.patch is not None else 0

        # Check if pre-minor release
        if patch == 0 and self.release is not None:
            return self.clone(patch=0)

        # Otherwise increment minor and return version with patch to zero
        minor = self.minor + 1
        return self.clone(minor=minor, patch=0)

    def next_patch(self) -> "Version":
        """
        Return next patch version.

        Returns:
            Next patch version.
        """
        patch = self.patch if self.patch is not None else 0

        # Check if pre-patch release
        if self.release is not None:
            return self.clone(patch=patch)

        # Otherwise increment patch and return version
        patch += 1
        return self.clone(patch=patch)

    def __eq__(self, other) -> bool:
        """
        Return True if versions are equals.

        Args:
            other: An other version

        Returns:
            True if equals
        """
        return self._cmp(other) == 0

    def __lt__(self, other):
        """
        Test if this version is less than an other.

        Args:
            other: An other version

        Returns:
            True if less than other
        """
        return self._cmp(other) == -1

    def __le__(self, other):
        """
        Test if this version is less or equals than an other.

        Args:
            other: An other version

        Returns:
            True if less or equals than other
        """
        return self._cmp(other) <= 0

    def __gt__(self, other):
        """
        Test if this version is greater than another.

        Args:
            other: An other version

        Returns:
            True if greater
        """
        return self._cmp(other) == 1

    def __ge__(self, other):
        """
        Test if this version is greater or equals than another.

        Args:
            other: An other version

        Returns:
            True if greater or equals
        """
        return self._cmp(other) >= 0
