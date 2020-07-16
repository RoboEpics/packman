from re import search

from repo2docker.buildpacks.r import RBuildPack

from .base import filter_files


class ModifiedRBuildPack(RBuildPack):
    def get_command(self):
        files = list(filter(lambda f: search(r'^install\.[rR]$', f) is None, filter_files(r'\.[rR]$')))
        if len(files) < 1:
            raise RuntimeError("No R script found to run! Aborting dockerization...")
        elif len(files) > 1:
            raise RuntimeError("Found multiple R scripts and can't decide which one to run! Aborting dockerization...")
        return files[0]
