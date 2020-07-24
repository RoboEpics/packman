from os import path

from repo2docker.buildpacks.python import PythonBuildPack

from ..base import DetectByFilenamePatternMixin, find_first_file_by_pattern


class IPythonNotebookBuildPack(DetectByFilenamePatternMixin, PythonBuildPack):
    eligible_filename_pattern = r"\.ipynb$"

    def get_build_script_files(self):
        files = super().get_build_script_files()
        files[path.join(path.dirname(__file__), 'run-ipynb.py')] = '${REPO_DIR}/run-ipynb.py'
        return files

    def get_command(self):
        notebook_file = find_first_file_by_pattern(self.eligible_filename_pattern)
        return '${REPO_DIR}/run-ipynb.py "%s"' % notebook_file
