from repo2docker.buildpacks.python import PythonBuildPack

from .conda import PythonRunCommandDetectorMixin


class ModifiedPythonBuildPack(PythonRunCommandDetectorMixin, PythonBuildPack):
    pass
