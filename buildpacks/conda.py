from re import search, MULTILINE

from repo2docker.buildpacks.conda import CondaBuildPack

from .base import filter_files


class PythonRunCommandDetectorMixin:
    def get_command(self):
        """
        Tries to find the project's main method and it's package and returns a command with them to be run.
        """
        main_file = None
        for file in filter_files(r"\.py$"):
            with open(file) as f:
                content = f.read()
                if search(r"^if\s+__name__\s*==\s*[\"']__main__[\"']\s*:", content, flags=MULTILINE) is not None:
                    main_file = file
                    break

        if main_file is None:
            raise RuntimeError("Could not find main file! Aborting dockerization...")

        return ["python", main_file]


class ModifiedCondaBuildPack(PythonRunCommandDetectorMixin, CondaBuildPack):
    pass
