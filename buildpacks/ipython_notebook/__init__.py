from repo2docker.buildpacks.python import PythonBuildPack

from ..base import DetectByFilenamePatternMixin, find_first_file_by_pattern


class IPythonNotebookBuildPack(DetectByFilenamePatternMixin, PythonBuildPack):
    eligible_filename_pattern = r"\.ipynb$"

    def get_preassemble_script_files(self):
        files = super().get_preassemble_script_files()
        files['./run-ipynb.py'] = './run-ipynb.py'
        return files

    def get_command(self):
        notebook_file = find_first_file_by_pattern(self.eligible_filename_pattern)
        return ["./run-ipynb.py", notebook_file]
