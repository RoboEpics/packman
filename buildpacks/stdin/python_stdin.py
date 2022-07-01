from repo2docker.buildpacks.base import BaseImage

from buildpacks.conda import find_python_main_file


TEMPLATE = """
FROM python:3.10-slim

ENV PYTHONUNBUFFERED 1

WORKDIR /root

{% for src, dst in build_script_files|dictsort %}
COPY {{ src }} {{ dst }}
chmod +x {{ dst }}
{% endfor -%}

COPY src/ .

CMD {{ command }}
"""


class Python310STDINBuildPack(BaseImage):
    template = TEMPLATE

    def get_build_script_files(self):
        return {
            "/home/worker/buildpacks/stdin/python-tester.sh": "python-tester.sh"
        }

    def get_command(self):
        """
        Tries to find the project's main method and it's package and returns a command with them to be run.
        """
        main_file = find_python_main_file()
        return "mv %s main.py && ./python-tester.sh" % main_file
