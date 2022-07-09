from re import search, MULTILINE

from repo2docker.buildpacks.conda import CondaBuildPack

from .base import filter_files


def find_python_main_file():
    count = 0
    for file in filter_files(r"\.py$"):
        count += 1
        with open(file) as f:
            content = f.read()
            if search(r"^if\s+__name__\s*==\s*[\"']__main__[\"']\s*:", content, flags=MULTILINE) is not None:
                return file

    # If there was only one Python file in the project, return it anyway
    if count == 1:
        return file

    raise RuntimeError("Could not find main file! Aborting dockerization...")


class PythonRunCommandDetectorMixin:
    def get_command(self):
        """
        Tries to find the project's main method and it's package and returns a command with them to be run.
        """
        return ["python", find_python_main_file()]


class ModifiedCondaBuildPack(PythonRunCommandDetectorMixin, CondaBuildPack):
    pass
