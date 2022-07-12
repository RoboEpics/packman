from repo2docker.buildpacks.base import BaseImage

from buildpacks.base import filter_files


def find_erlang_main_file():
    for file in filter_files(r"\.erl$"):
        return file

    raise RuntimeError("Could not find main file! Aborting dockerization...")


TEMPLATE = """
FROM erlang:25

RUN apt-get update -q && apt-get install -qqy bc time && rm -rf /var/lib/apt/lists/*

WORKDIR /root

{% if env -%}
{% for item in env -%}
ENV {{item[0]}} {{item[1]}}
{% endfor -%}
{% endif -%}

{% for src, dst in build_script_files|dictsort %}
COPY {{ src }} {{ dst }}
RUN chmod +x {{ dst }}
{% endfor -%}

COPY src/ .

CMD {{ command }}
"""


class Erlang25STDINBuildPack(BaseImage):
    template = TEMPLATE

    def get_build_script_files(self):
        return {
            "/home/worker/buildpacks/stdin/erlang-tester.sh": "erlang-tester.sh"
        }

    def get_env(self):
        return [('ENTRY_FILE', find_erlang_main_file())]

    def get_command(self):
        """
        Tries to find the project's main method and it's package and returns a command with them to be run.
        """
        return "./erlang-tester.sh"
