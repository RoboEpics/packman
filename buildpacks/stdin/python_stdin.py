from repo2docker.buildpacks.base import BaseImage

from buildpacks.conda import find_python_main_file


TEMPLATE = """
FROM python:3.10-slim

ENV PYTHONUNBUFFERED 1

# Allow target path repo is cloned to be configurable
ARG REPO_DIR=${HOME}
ENV REPO_DIR ${REPO_DIR}
WORKDIR ${REPO_DIR}

COPY stdin/python-tester.sh python-tester.sh
COPY src/ .

CMD {{ command }}
"""


class Python310STDINBuildPack(BaseImage):
    template = TEMPLATE

    def get_command(self):
        """
        Tries to find the project's main method and it's package and returns a command with them to be run.
        """
        main_file = find_python_main_file()
        return ["mv", main_file, "main.py", "&&", "./python-tester.sh"]
