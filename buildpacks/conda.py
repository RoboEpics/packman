from repo2docker.buildpacks.conda import CondaBuildPack

from .base import filter_files


class PythonRunCommandDetectorMixin:
    def get_command(self):
        """
        Tries to find the project's main method and it's package and returns a command with them to be run.
        """
        main_file = None
        print(list(filter_files(r"\.py$")))
        print(list(filter_files(r"*")))
        for file in filter_files(r"\.py$"):
            with open(file) as f:
                content = f.read()
                print(content)
                if content.find('if __name__ == "__main__"') != -1:  # FIXME use regex to match arbitrary whitespaces and different method signatures
                    main_file = file
                    break

        if main_file is None:
            raise RuntimeError("Could not find main file! Aborting dockerization...")

        return ["python", main_file]


class ModifiedCondaBuildPack(PythonRunCommandDetectorMixin, CondaBuildPack):
    pass
