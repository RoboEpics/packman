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
            env = YAML().load(f)
            # check if the env file is empty, if so instantiate an empty dictionary.
            if env is None:
                env = {}
            # check if the env file provided a dict-like thing not a list or other data structure.
            if not isinstance(env, Mapping):
                raise TypeError("Custom run config file should contain a dictionary. Got %r" % type(env))
            self._custom_run_yaml = env

        return self._custom_run_yaml

    def get_base_image(self):
        """Set the user-provided base image name."""
        return self.custom_run_yaml['languages']

    def get_assemble_scripts(self):
        """Add user-provided build-phase commands to parent assemble commands."""
        assemble_scripts = super().get_assemble_scripts()
        assemble_scripts.extend(list(map(lambda c: ("${NB_USER}", c), self.custom_run_yaml['build'])))
        return assemble_scripts

    def get_command(self):
        """Set user-provided run command."""
        return self.custom_run_yaml['run']

    def detect(self):
        """Check if current repo has the config file needed to build it with the custom run BuildPack."""
        return any((os.path.exists(self.binder_path(file)) for file in self.eligible_config_filenames)) and super().detect()
