#!/usr/bin/env python3
import os
import logging
from subprocess import Popen, PIPE
from json import loads
from repo2docker.app import Repo2Docker
from repo2docker.buildpacks import (
    CondaBuildPack,
    DockerBuildPack,
    JuliaProjectTomlBuildPack,
    JuliaRequireBuildPack,
    NixBuildPack,
    PipfileBuildPack,
    PythonBuildPack,
    RBuildPack,
)
from sentry_sdk import capture_exception

logger = logging.getLogger('runner')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'packman.settings')

import django
django.setup()

from django.conf import settings
from django.utils.module_loading import import_string

from problem.models import Submission
from leaderboard.models import Leaderboard

from buildpacks import *

buildpacks = [
    DockerBuildPack,
    CustomRunBuildPack,
    MakeBuildPack,

    JuliaProjectTomlBuildPack,
    JuliaRequireBuildPack,

    NixBuildPack,

    RBuildPack,

    CondaBuildPack,
    PipfileBuildPack,
    PythonBuildPack,

    JavaNoBuildToolBuildPack,

    GoBuildPack,

    CMakeBuildPack,
    CPPBuildPack
]


def create_docker_image(gitlab_repo, commit_hash, image_name):
    # Create Docker image from git repository using jupyter-repo2docker
    r2d = Repo2Docker()

    r2d.repo = f"https://oauth2:{settings.GIT_ADMIN_TOKEN}@{settings.GIT_HOST}/{gitlab_repo}.git"
    r2d.ref = commit_hash
    r2d.output_image_spec = image_name = '/'.join((settings.DOCKER_REGISTRY_HOST, image_name))
    r2d.user_id = 2000
    r2d.user_name = 'jovyan'
    r2d.buildpacks = buildpacks

    r2d.initialize()
    r2d.build()

    run_command = r2d.picked_buildpack.get_command()

    return image_name, run_command


def push_image_to_registry(image_name):
    password = Popen(('cat', settings.DOCKER_REGISTRY_PASSWORD_FILE), stdout=PIPE)
    if password.wait() != 0:
        raise ChildProcessError("Password extraction failed!")

    if Popen(('docker', 'login', '--username', settings.DOCKER_REGISTRY_USERNAME, '--password-stdin', settings.DOCKER_REGISTRY_HOST), stdin=password.stdout, stdout=PIPE, stderr=PIPE).wait() != 0:
        raise ChildProcessError("Docker login failed!")

    if Popen(('docker', 'push', image_name), stdout=PIPE, stderr=PIPE).wait() != 0:
        raise ChildProcessError("Docker push failed!")


def handle_new_message(channel, method, properties, body):
    logger.info("Received new message from queue...")

    request = loads(body)
    logger.debug("Message content: %s" % str(request))

    try:
        submission = Submission.objects.get(id=request['submission_id'])
    except Submission.DoesNotExist:
        logger.warning("No submission with the given exists! Dropping message from queue...")
        channel.basic_ack(method.delivery_tag)
        return

    # Create Docker image from Gitlab repository
    logger.debug("Creating Docker image for submission %d..." % submission.id)

    submission.status = Submission.SubmissionStatus.IMAGE_BUILD_STARTED
    submission.save()

    image_name, run_command = create_docker_image(submission.generate_git_repo_path(), submission.reference, submission.generate_image_name())

    submission.status = Submission.SubmissionStatus.IMAGE_BUILD_SUCCESSFUL
    submission.command = ' '.join(run_command)
    submission.save()

    logger.debug("Successfully created Docker image for submission %d!" % submission.id)

    # Push the image to Docker registry
    logger.debug("Pushing Docker image for submission %d..." % submission.id)
    try:
        push_image_to_registry(image_name)

        submission.status = Submission.SubmissionStatus.IMAGE_READY
        submission.save()

        # Reset operator's rating for this problem, FIXME it's better to be in a post_save signal
        Leaderboard.objects.get(
            problem_id=submission.problem_id
        ).leaderboard_function.leaderboardtrueskillrank_set.update_or_create(
            defaults={'mu': 25.0, 'sigma': 25 / 3},
            owner_id=submission.owner_id
        )

        channel.basic_ack(method.delivery_tag)

        logger.debug("Successfully pushed Docker image for submission %d!" % submission.id)
    except ChildProcessError:
        capture_exception()

        submission.status = Submission.SubmissionStatus.IMAGE_PUSH_FAILED
        submission.save()

        logger.error("Something went wrong while pushing Docker image for submission %d!" % submission.id)


if __name__ == "__main__":
    # Initialize message queue client
    client = import_string(settings.QUEUE_CLIENT)(settings.QUEUE_CLIENT_API_HOST)

    logger.info('Waiting on messages from queue "%s"...' % settings.QUEUE_NAME)
    client.pull(handle_new_message, settings.QUEUE_NAME)
