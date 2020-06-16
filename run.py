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
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dockerizer.settings')

import django
django.setup()

from django.conf import settings
from django.utils.module_loading import import_string

from problem.models import Submission

from buildpacks import *

buildpacks = [
    DockerBuildPack,
    CustomRunBuildPack,

    JuliaProjectTomlBuildPack,
    JuliaRequireBuildPack,

    NixBuildPack,

    RBuildPack,

    CondaBuildPack,
    PipfileBuildPack,
    PythonBuildPack,

    JavaNoBuildToolBuildPack,

    GoBuildPack
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

    return image_name


def push_image_to_registry(image_name):
    password = Popen(('cat', settings.DOCKER_REGISTRY_PASSWORD_FILE), stdout=PIPE)
    if password.wait() != 0:
        capture_exception()
        return False

    login = Popen(('docker', 'login', '--username', settings.DOCKER_REGISTRY_USERNAME, '--password-stdin', settings.DOCKER_REGISTRY_HOST), stdin=password.stdout, stdout=PIPE, stderr=PIPE)
    if login.wait() != 0:
        capture_exception()
        return False

    push = Popen(('docker', 'push', image_name), stdout=PIPE, stderr=PIPE)
    if push.wait() != 0:
        capture_exception()
        return False

    return True


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

    image_name = create_docker_image(submission.generate_git_repo_path(), submission.reference, submission.generate_image_name())

    submission.status = Submission.SubmissionStatus.IMAGE_BUILD_SUCCESSFUL
    submission.save()

    logger.debug("Successfully created Docker image for submission %d!" % submission.id)

    # Push the image to Docker registry
    logger.debug("Pushing Docker image for submission %d..." % submission.id)
    status = push_image_to_registry(image_name)

    if status:
        submission.status = Submission.SubmissionStatus.IMAGE_READY
        submission.save()

        channel.basic_ack(method.delivery_tag)

        logger.debug("Successfully pushed Docker image for submission %d!" % submission.id)
    else:
        submission.status = Submission.SubmissionStatus.IMAGE_PUSH_FAILED
        submission.save()

        logger.debug("Something went wrong while pushing Docker image for submission %d!" % submission.id)


if __name__ == "__main__":
    # Initialize message queue client
    client = import_string(settings.QUEUE_CLIENT)(settings.QUEUE_CLIENT_API_HOST)

    logger.info('Waiting on messages from queue "%s"...' % settings.QUEUE_NAME)
    client.pull(handle_new_message, settings.QUEUE_NAME)
