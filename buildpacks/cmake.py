from .make import MakeBuildPack


class CMakeBuildPack(MakeBuildPack):
    eligible_config_filenames = {"CMakeLists.txt"}

    def get_base_image(self):
        return "celiangarcia/gcc8-cmake:3.15.7"

    def get_assemble_scripts(self):
        """
        Simply runs `cmake .` and `make`.
        """
        assemble_scripts = super().get_assemble_scripts()

        # `cmake` command should be run before `make`.
        assemble_scripts.insert(len(assemble_scripts) - 1, ("${NB_USER}", 'cmake .'))

        return assemble_scripts
