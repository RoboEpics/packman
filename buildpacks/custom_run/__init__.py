import os
import shlex
from collections import Mapping

from repo2docker.buildpacks.base import BuildPack
from ruamel.yaml import YAML

TEMPLATE = r"""
FROM {{ base_image }}

# Use bash as default shell, rather than sh
ENV SHELL /bin/bash

# Set up user
ARG NB_USER
ARG NB_UID
ENV USER ${NB_USER}
ENV HOME /home/${NB_USER}

# Allow target path of repo that is cloned to be configurable
ARG REPO_DIR=${HOME}
ENV REPO_DIR ${REPO_DIR}
WORKDIR ${REPO_DIR}

RUN groupadd \
        --gid ${NB_UID} \
        ${NB_USER} && \
    useradd \
        --comment "Default user" \
        --create-home \
        --gid ${NB_UID} \
        --no-log-init \
        --shell /bin/bash \
        --uid ${NB_UID} \
        ${NB_USER}

USER root
COPY src/ ${REPO_DIR}
RUN chown -R ${NB_USER}:${NB_USER} ${REPO_DIR}

# We want to allow two things:
#   1. If there's a .local/bin directory in the repo, things there
#      should automatically be in path
#   2. postBuild and users should be able to install things into ~/.local/bin
#      and have them be automatically in path
#
# The XDG standard suggests ~/.local/bin as the path for local user-specific
# installs. See https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
ENV PATH ${HOME}/.local/bin:${REPO_DIR}/.local/bin:${PATH}

{% if build_env -%}
# Environment variables required for build
{% for item in build_env -%}
ENV {{item[0]}} {{item[1]}}
{% endfor -%}
{% endif -%}

# Run assemble scripts! These will actually turn the specification
# in the repository into an image.
{% for sd in assemble_script_directives -%}
{{ sd }}
{% endfor %}

{% if env -%}
# The rest of the environment
{% for item in env -%}
ENV {{item[0]}} {{item[1]}}
{% endfor -%}
{% endif -%}

# Container image Labels!
# Put these at the end, since we don't want to rebuild everything
# when these change! Did I mention I hate Dockerfile cache semantics?
{% for k, v in labels|dictsort %}
LABEL {{k}}="{{v}}"
{%- endfor %}

# We always want containers to run as non-root
USER ${NB_USER}

# Add start script
{% if start_script is not none -%}
RUN chmod +x "{{ start_script }}"
ENV R2D_ENTRYPOINT "{{ start_script }}"
{% endif -%}

# Add entrypoint
COPY /repo2docker-entrypoint /usr/local/bin/repo2docker-entrypoint
ENTRYPOINT ["/usr/local/bin/repo2docker-entrypoint"]

# Specify the default command to run
CMD [{% for c in command -%} "{{ c }}"{{ ", " if not loop.last }}{% endfor -%}]

{% if appendix -%}
# Appendix:
{{ appendix }}
{% endif %}
"""


class CustomRunBuildPack(BuildPack):
    template = TEMPLATE
    eligible_config_filenames = {"custom-run.yaml", "custom_run.yaml", "custom-run.yml", "custom_run.yml"}
    _custom_run_yaml = None

    @property
    def custom_run_yaml(self):
        if self._custom_run_yaml is not None:
            return self._custom_run_yaml

        custom_run_yaml = None
        for file in self.eligible_config_filenames:
            _temp = self.binder_path(file)
            if os.path.exists(_temp):
                custom_run_yaml = _temp

        if custom_run_yaml is None:
            self._custom_run_yaml = {}
            return self._custom_run_yaml

        with open(custom_run_yaml) as f:
            config = YAML().load(f)
            # check if the config file is empty, if so instantiate an empty dictionary.
            if config is None:
                config = {}
            # check if the config file provided a dict-like thing, not a list or other data structure.
            if not isinstance(config, Mapping):
                raise TypeError("Custom run config file should contain a dictionary. Got %r" % type(config))
            self._custom_run_yaml = config

        return self._custom_run_yaml

    def get_base_image(self):
        """Set the user-provided base image name."""
        return self.custom_run_yaml['language']

    def get_build_env(self):
        return super().get_build_env() + list(self.custom_run_yaml['build']['env'].items())

    def get_env(self):
        return super().get_env() + list(self.custom_run_yaml['run']['env'].items())

    def get_assemble_scripts(self):
        """Add user-provided build-phase commands to parent assemble commands."""
        assemble_scripts = super().get_assemble_scripts()
        assemble_scripts.extend(list(map(lambda c: ("root", c), self.custom_run_yaml['build']['commands'])))
        return assemble_scripts

    def get_command(self):
        """Set user-provided run command."""
        return shlex.split(self.custom_run_yaml['run']['command'])

    def detect(self):
        """Check if current repo has the config file needed to build it with the custom run BuildPack."""
        return any((os.path.exists(self.binder_path(file)) for file in self.eligible_config_filenames)) and super().detect()
