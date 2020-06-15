import os
from collections import Mapping

from repo2docker.buildpacks.base import BuildPack
from ruamel.yaml import YAML


class CustomRunBuildPack(BuildPack):
    eligible_config_filenames = {"custom-run.yaml", "custom-run.yml"}
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
        assemble_scripts.extend(list(map(lambda c: ("root", c), self.custom_run_yaml['build'])))
        return assemble_scripts

    def get_command(self):
        """Set user-provided run command."""
        return self.custom_run_yaml['run']

    def detect(self):
        """Check if current repo has the config file needed to build it with the custom run BuildPack."""
        return any((os.path.exists(self.binder_path(file)) for file in self.eligible_config_filenames)) and super().detect()
