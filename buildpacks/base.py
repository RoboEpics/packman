from os import path, walk
from re import search

from repo2docker.buildpacks.base import BuildPack


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
        return any(filter(lambda x: search(self.eligible_filename_pattern, x) is not None, (
            val for sublist in ((path.join(i[0], j) for j in i[2]) for i in walk('.')) for val in sublist
        )))


class BaseSimpleBuildPack(DetectByConfigFileMixin, BuildPack):
    pass


class BaseSmartBuildPack(DetectByFilenamePatternMixin, BuildPack):
    pass
