import os

from repo2docker.buildpacks.conda import CondaBuildPack


class PythonRunCommandDetectorMixin:
    def get_command(self):
        """
        Tries to find the project's main method and it's package and returns a command with them to be run.
        """
        main_file = None
        for file in filter(lambda x: x.endswith('.py'), (val for sublist in ((os.path.join(i[0], j) for j in i[2]) for i in os.walk('.')) for val in sublist)):
            with open(file) as f:
                content = f.read()
                if content.find('if __name__ == "__main"') != -1:  # FIXME use regex to match arbitrary whitespaces and different method signatures
                    main_file = file
                    break

        if main_file is None:
            raise RuntimeError("Could not find main file! Aborting dockerization...")

        return ["python", main_file]


class ModifiedCondaBuildPack(PythonRunCommandDetectorMixin, CondaBuildPack):
    pass
