from os import path, walk
from re import search

from repo2docker.buildpacks.base import BaseImage


def filter_files(pattern):
    return filter(lambda x: search(pattern, x) is not None, (
        val for sublist in ((path.join(i[0], j) for j in i[2]) for i in walk('.')) for val in sublist
    ))


def find_first_file_by_pattern(pattern):
    try:
        return next(filter_files(pattern))
    except StopIteration:
        return None


class CompileBuildPackMixin:
    def get_command(self):
        """
        Returns the compiled file to be executed.
        """
        return ["./bin/out"]


class DetectByConfigFileMixin:
    eligible_config_filenames = set()

    def detect(self):
        """Check if current repo has a config file needed to build it with this BuildPack."""
        return any((path.exists(self.binder_path(file)) for file in self.eligible_config_filenames))


class DetectByFilenamePatternMixin:
    eligible_filename_pattern = ""

    def detect(self):
        """Check if there are any eligible files in the repository."""
        return any(filter_files(self.eligible_filename_pattern))


class BaseSimpleBuildPack(DetectByConfigFileMixin, BaseImage):
    pass


class BaseSmartBuildPack(DetectByFilenamePatternMixin, BaseImage):
    pass
