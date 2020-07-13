import re
from os import path

from buildpacks.base import BaseSmartBuildPack, filter_files


class JavaNoBuildToolBuildPack(BaseSmartBuildPack):
    eligible_filename_pattern = r"\.java$"

    def get_base_image(self):
        """OpenJDK image is based on buildpack-deps image, so it's compatible with repo2docker."""
        return "openjdk:14-buster"

    def get_assemble_scripts(self):
        """
        Gets the list of all the .java files and tries to compile them.
        """
        assemble_scripts = super().get_assemble_scripts()
        assemble_scripts.extend([
            ("${NB_USER}", 'find -name "*.java" > sources.txt'),
            ("${NB_USER}", "javac @sources.txt -d out"),
            ("${NB_USER}", "rm -f sources.txt")
        ])
        return assemble_scripts

    def get_command(self):
        """
        Tries to find the project's main method and it's package and returns a command with them to be run.
        """
        main_class = None
        for file in filter_files(self.eligible_filename_pattern):
            with open(file) as f:
                content = f.read()
                if content.find('public static void main(String[] args)') != -1:  # FIXME use regex to match arbitrary whitespaces and different method signatures
                    # Try to find the main class's package name
                    m = re.search(r'package (?P<package_name>\w+);\s*\n', content)  # FIXME should be checked to be at the start of the line with ^
                    package = ""
                    if m:
                        package = m.group('package_name') + '.'

                    # Create the path of the main class
                    main_class = package + path.basename(file)[:-5]
                    break

        if main_class is None:
            raise RuntimeError("No file with a main method found! Aborting dockerization...")

        return ["java", "-cp", "out", main_class]
