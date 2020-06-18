from buildpacks.base import BaseSmartBuildPack, CompileBuildPackMixin


class CPPBuildPack(CompileBuildPackMixin, BaseSmartBuildPack):
    eligible_files_pattern = r"\.cpp$"

    def get_base_image(self):
        """GCC image is based on buildpack-deps image, so it's compatible with repo2docker."""
        return "gcc:10"

    def get_assemble_scripts(self):
        """
        Gets the list of all the .cpp files and tries to compile them.
        """
        assemble_scripts = super().get_assemble_scripts()
        assemble_scripts.extend([
            ("${NB_USER}", 'mkdir bin'),
            ("${NB_USER}", r'find -name "*.cpp" | tr "\n" " " | xargs g++ -o bin/out')
        ])
        return assemble_scripts
