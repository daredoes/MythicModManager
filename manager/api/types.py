from __future__ import annotations

import re
from distutils.version import StrictVersion


class PackageReference:
    VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")

    def __init__(self, namespace, name, version=None):
        """
        :param str namespace: The namespace of the referenced package
        :param str name: The name of the referenced package
        :param version: The version of the referenced package
        :type version: StrictVersion or None
        """
        self.namespace = namespace
        self.name = name
        self.version = version

    def __str__(self):
        if self.version:
            return f"{self.namespace}-{self.name}-{self.version}"
        else:
            return f"{self.namespace}-{self.name}"

    def is_same_package(self, other) -> bool:
        """
        Check if another package reference belongs to the same package as this
        one

        :param PackageReference other: The package to check against
        :return: True if matching, False otherwise
        :rtype: bool
        :raises ValueError: If the other object is not a PackageReference
        """
        return self.namespace == other.namespace and self.name == other.name

    def is_same_version(self, other) -> bool:
        """
        Check if another package reference is of the same package and version as
        this one

        :param PackageReference other: The package to check against
        :return: True if matching, False otherwise
        :rtype: bool
        :raises ValueError: If the other object is not a PackageReference
        """
        return self.is_same_package(other) and self.version == other.version

    def __eq__(self, other):
        if isinstance(other, PackageReference):
            return self.is_same_version(other)
        return False

    @classmethod
    def parse(self, reference_string) -> PackageReference:
        """
        - Packages references are in format {namespace}-{name}-{version}
        - Namespace may contain dashes, whereas name and version can not
        - Version might not be included

        This means we must parse the reference string backwards, as there is no
        good way to know when the namespace ends and the package name starts.

        :param str reference_string: The package reference string
        :return: A parsed PackageReferenced object
        :rtype: PackageReference
        :raises ValueError: If the reference string is in an invalid format
        """

        version_string = reference_string[-5:]
        version = None
        if re.match(self.VERSION_PATTERN, version_string):
            if reference_string.split("-")[-1] != version_string:
                raise ValueError("Invalid package reference string")
            version = StrictVersion(version_string)
            reference_string = reference_string[:-6]

        name = reference_string.split("-")[-1]
        namespace = "-".join(reference_string.split("-")[:-1])

        if not (namespace and name):
            raise ValueError("Invalid package reference string")

        return PackageReference(namespace=namespace, name=name, version=version)
