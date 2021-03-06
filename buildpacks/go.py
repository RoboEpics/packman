from buildpacks.base import BaseSmartBuildPack, CompileBuildPackMixin, filter_files


class GoBuildPack(CompileBuildPackMixin, BaseSmartBuildPack):
    eligible_filename_pattern = r"\.go$"

    def get_base_image(self):
        """Golang image is based on buildpack-deps image, so it's compatible with repo2docker."""
        return "golang:buster"

    def get_assemble_scripts(self):
        """
        Gets the list of all the .go files and tries to compile them.
        """
        main_file = None
        for file in filter_files(self.eligible_filename_pattern):
            with open(file) as f:
                content = f.read()
                if content.find('package main') != -1 and content.find('func main()') != -1:
                    main_file = file
                    break

        assemble_scripts = super().get_assemble_scripts()
        assemble_scripts.extend([
            ("${NB_USER}", 'go get ./...'),
            ("${NB_USER}", 'go build -o bin/out ' + main_file)
        ])
        return assemble_scripts
