"""
Test semantic versioning in the package
"""

import re

from guidelight.version import get_version


def test_semver():
    """
    Ensure that the current version is a semantic version
    """
    semver = re.compile(
        r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"  # noqa
    )

    assert semver.match(get_version(short=False)) is not None
    assert semver.match(get_version(short=True)) is not None
