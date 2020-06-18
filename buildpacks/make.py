from buildpacks.base import BaseSimpleBuildPack, CompileBuildPackMixin


class MakeBuildPack(CompileBuildPackMixin, BaseSimpleBuildPack):
    eligible_config_filenames = {"Makefile"}

    def get_base_image(self):
        """GCC image is based on buildpack-deps image, so it's compatible with repo2docker."""
        return "gcc:10"

    def get_assemble_scripts(self):
        """
        Simply runs `make`.
        """
        assemble_scripts = super().get_assemble_scripts()
        assemble_scripts.extend([
            ("${NB_USER}", 'make')
        ])
        return assemble_scripts
