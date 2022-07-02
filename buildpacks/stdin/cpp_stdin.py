from buildpacks.cpp import CPPBuildPack


TEMPLATE = """
FROM gcc:12

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


class ErlangSTDINBuildPack(CPPBuildPack):
    template = TEMPLATE

    def get_build_script_files(self):
        return {
            "/home/worker/buildpacks/stdin/cpp-tester.sh": "cpp-tester.sh"
        }

    def get_env(self):
        return [('ENTRY_FILE', './bin/out')]

    def get_command(self):
        """
        Tries to find the project's main method and it's package and returns a command with them to be run.
        """
        return "./cpp-tester.sh"
