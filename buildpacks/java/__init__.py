import re
import os
from os import path

from repo2docker.buildpacks.base import BuildPack


class JavaNoBuildToolBuildPack(BuildPack):
    def get_build_script_files(self):
        """
        Adds the JDK installer script.
        """
        files = super().get_build_script_files()
        files['java/install-jdk.bash'] = '/tmp/install-jdk.bash'
        return files

    def get_build_scripts(self):
        """
        Returns the execution of the JDK installer script as root user.
        """
        return super().get_build_scripts() + [
            (
                "root",
                r"""
                bash /tmp/install-jdk.bash && \
                rm /tmp/install-jdk.bash
                """,
            )
        ]

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
        for file in filter(lambda x: x.endswith('.java'), (val for sublist in ((os.path.join(i[0], j) for j in i[2]) for i in os.walk('.')) for val in sublist)):
            with open(file) as f:
                content = f.read()
                if content.find('public static void main(String[] args)') != -1:  # FIXME use regex to match arbitrary whitespaces and different method signatures
                    # Try to find the main class's package name
                    m = re.search(r'package (?P<package_name>\w+);\s+\n', content)
                    package = ""
                    if m:
                        package = m.group('package_name') + '.'

                    # Create the path of the main class
                    main_class = package + path.basename(file)[:-5]
                    break

        if main_class is None:
            raise RuntimeError("No file with a main method found! Aborting dockerization...")

        return "java -cp out " + main_class

    def detect(self):
        """Check if there are any .java files in the repository."""
        try:
            next(filter(lambda x: x.endswith('.java'), (val for sublist in ((os.path.join(i[0], j) for j in i[2]) for i in os.walk('.')) for val in sublist)))
            return True
        except StopIteration:
            return False