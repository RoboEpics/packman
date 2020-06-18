import os

from repo2docker.buildpacks.base import BuildPack


class MakeBuildPack(BuildPack):
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

    def get_command(self):
        """
        Returns the compiled file to be executed.
        """
        return ["./out"]

    def detect(self):
        """Check if there are any Makefiles in the repository."""
        try:
            next(filter(lambda x: x == 'Makefile', (val for sublist in ((os.path.join(i[0], j) for j in i[2]) for i in os.walk('.')) for val in sublist)))
            return True
        except StopIteration:
            return False
