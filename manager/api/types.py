from __future__ import annotations

from distutils.version import StrictVersion

from cached_property import cached_property


class PackageReference:
    def __init__(self, namespace, name, version=None):
        """
        :param str namespace: The namespace of the referenced package
        :param str name: The name of the referenced package
        :param version: The version of the referenced package
        :type version: StrictVersion or str or None
        """
        self.namespace = namespace
        self.name = name
        if version is not None and not isinstance(version, StrictVersion):
            version = StrictVersion(version)
        self.version = version

    def __str__(self) -> str:
        if self.version:
            return f"{self.namespace}-{self.name}-{self.version_str}"
        else:
            return f"{self.namespace}-{self.name}"

    def __repr__(self) -> str:
        return f"<PackageReference: {str(self)}>"

    @property
    def version_str(self):
        if self.version is not None:
            return ".".join(str(x) for x in self.version.version)
        return ""

    def is_same_package(self, other) -> bool:
        """
        Check if another package reference belongs to the same package as this
        one

        :param other: The package to check against
        :type other: PackageReference or str
        :return: True if matching, False otherwise
        :rtype: bool
        """
        if isinstance(other, str):
            other = PackageReference.parse(other)
        return self.namespace == other.namespace and self.name == other.name

    def is_same_version(self, other) -> bool:
        """
        Check if another package reference is of the same package and version as
        this one

        :param other: The package to check against
        :type other: PackageReference or str
        :return: True if matching, False otherwise
        :rtype: bool
        """
        if isinstance(other, str):
            other = PackageReference.parse(other)
        if not self.is_same_package(other):
            return False
        try:
            return self.version == other.version
        except AttributeError:
            return False

    def __eq__(self, other):
        if isinstance(other, PackageReference):
            return self.is_same_version(other)
        return False

    def __gt__(self, other):
        if isinstance(other, PackageReference):
            return self.version > other.version
        return super().__gt__(other)

    def __lt__(self, other):
        if isinstance(other, PackageReference):
            return self.version < other.version
        return super().__lt__(other)

    def __hash__(self):
        return hash(str(self))

    @classmethod
    def parse(cls, unparsed) -> PackageReference:
        """
        - Packages references are in format {namespace}-{name}-{version}
        - Namespace may contain dashes, whereas name and version can not
        - Version might not be included

        This means we must parse the reference string backwards, as there is no
        good way to know when the namespace ends and the package name starts.

        :param str unparsed: The package reference string
        :return: A parsed PackageReferenced object
        :rtype: PackageReference
        :raises ValueError: If the reference string is in an invalid format
        """
        if isinstance(unparsed, PackageReference):
            return unparsed

        version_string = unparsed.split("-")[-1]
        version = None
        if version_string.count(".") > 0:
            if unparsed.count(".") != 2:
                raise ValueError("Invalid package reference string")
            if unparsed.count("-") < 2:
                raise ValueError("Invalid package reference string")
            version = StrictVersion(version_string)
            unparsed = unparsed[: -(len(version_string) + 1)]

        name = unparsed.split("-")[-1]
        namespace = "-".join(unparsed.split("-")[:-1])

        if not (namespace and name):
            raise ValueError("Invalid package reference string")

        return PackageReference(namespace=namespace, name=name, version=version)

    @cached_property
    def without_version(self) -> PackageReference:
        """
        Return this same package reference with version information removed

        :return: Versionless reference to the same package
        :rtype: PackageReference
        """
        if self.version:
            return PackageReference(namespace=self.namespace, name=self.name)
        return self

    def with_version(self, version) -> PackageReference:
        """
        Return this same package reference with a different version

        :return: A reference to this package's specific version
        :rtype: PackageReference
        """
        return PackageReference(
            namespace=self.namespace, name=self.name, version=version
        )
