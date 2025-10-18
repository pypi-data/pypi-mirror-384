# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Script for getting/bumping the next pre-release version.

"""
import pathlib
import sys

from qbraid_core.system.versions import get_prelease_version

if __name__ == "__main__":

    package_name = sys.argv[1]
    root = pathlib.Path(__file__).parent.parent.resolve()
    version = get_prelease_version(root, package_name)
    print(version)
