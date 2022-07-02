#!/usr/bin/env python3
import os
import logging
from subprocess import Popen, PIPE
from json import loads
from repo2docker.app import Repo2Docker
from repo2docker.buildpacks import (
    DockerBuildPack,
    JuliaProjectTomlBuildPack,
    JuliaRequireBuildPack,
    NixBuildPack,
    PipfileBuildPack
)
from sentry_sdk import capture_exception

logger = logging.getLogger('runner')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'packman.settings')

import django
django.setup()

from django.conf import settings
from django.utils.module_loading import import_string

from problem.models import Submission, ProblemCode
# from leaderboard.models import SimpleLeaderboard

from buildpacks import *
from buildpacks import stdin as stdin_buildpacks

buildpacks = [
    DockerBuildPack,
    CustomRunBuildPack,
    MakeBuildPack,

    JuliaProjectTomlBuildPack,
    JuliaRequireBuildPack,

    NixBuildPack,

    RBuildPack,

    IPythonNotebookBuildPack,
    CondaBuildPack,
    PipfileBuildPack,
    PythonBuildPack,

    JavaNoBuildToolBuildPack,

    GoBuildPack,

    CMakeBuildPack,
    CPPBuildPack
]

# Initialize message queue client
client = import_string(settings.QUEUE_CLIENT)(settings.QUEUE_SERVER_API_URL)


def create_docker_image(gitlab_repo, commit_hash, image_name, buildpack=None):
    # Create Docker image from git repository using jupyter-repo2docker
    r2d = Repo2Docker()

    r2d.repo = f"https://oauth2:{settings.GIT_ADMIN_TOKEN}@{settings.GIT_HOST}/{gitlab_repo}.git"
    r2d.ref = commit_hash
    r2d.output_image_spec = image_name = '/'.join((settings.DOCKER_REGISTRY_HOST, image_name))
    r2d.user_id = 2000
    r2d.user_name = 'jovyan'
    if buildpack is None:
        r2d.buildpacks = buildpacks
        r2d.default_buildpack = PythonBuildPack
    else:
        r2d.buildpacks = []
        r2d.default_buildpack = buildpack

    r2d.initialize()
    r2d.build()

    # run_command = r2d.picked_buildpack.get_command()
    run_command = None

    return image_name, run_command


def push_image_to_registry(image_name):
    # password = Popen(('cat', settings.DOCKER_REGISTRY_PASSWORD_FILE), stdout=PIPE)
    # if password.wait() != 0:
    #     raise ChildProcessError("Password extraction failed!")

    # if Popen(('docker', 'login', '--username', settings.DOCKER_REGISTRY_USERNAME, '--password-stdin', settings.DOCKER_REGISTRY_HOST), stdin=password.stdout, stdout=PIPE, stderr=PIPE).wait() != 0:
    #     raise ChildProcessError("Docker login failed!")

    if Popen(('docker', '--config', '/data/docker', 'push', image_name), stdout=PIPE, stderr=PIPE).wait() != 0:
        raise ChildProcessError("Docker push failed!")


def handle_new_message(channel, method_frame, header_frame, result):
    logger.info("Received a new message from queue...")

    request = loads(result)
    logger.debug("Message content: %s" % str(request))

    if 'code_id' in request:  # FIXME
        code = ProblemCode.objects.get(id=request['code_id'])
        try:
            image_name, run_command = create_docker_image(code.get_git_repo_path(), request['reference'],
                                                          "%s:%d" % (code.get_git_repo_path().lower(), code.id))

            logger.debug("Successfully created Docker image for ProblemCode %d!" % code.id)
        except Exception:
            capture_exception()
            logger.error("Something went wrong while building Docker image for ProblemCode %d!" % code.id)

            channel.basic_ack(method_frame.delivery_tag)
            # client.delete(result)

            return

        try:
            push_image_to_registry(image_name)

            logger.debug("Successfully pushed Docker image for ProblemCode %d!" % code.id)
        except ChildProcessError as e:
            capture_exception()

            logger.error("Something went wrong while pushing Docker image for ProblemCode %d: %s!" % (code.id, str(e)))

        channel.basic_ack(method_frame.delivery_tag)
        # client.delete(result)
        return

    try:
        submission = Submission.objects.get(id=request['submission_id'])
    except Submission.DoesNotExist:
        capture_exception()

        logger.error("No submission with the given id exists! Dropping message from queue...")

        channel.basic_ack(method_frame.delivery_tag)
        # client.delete(result)
        return

    enter = submission.problem_enter
    if enter is None:
        return

    # Create Docker image from Gitlab repository
    logger.debug("Creating Docker image for submission %d..." % submission.id)

    submission.status = Submission.SubmissionStatus.IMAGE_BUILD_STARTED
    submission.save()

    buildpack = None  # TODO this code was written in a rush for a specific competition. needs cleaning.
    if submission.runtime:
        if submission.runtime == "other":
            submission.status = Submission.SubmissionStatus.SUBMISSION_READY
            submission.save(skip_run=True)
            return
        buildpack = getattr(stdin_buildpacks, submission.runtime, None)

    try:
        image_name, run_command = create_docker_image(enter.code.get_git_repo_path(), submission.reference, submission.generate_image_name(), buildpack)
    except Exception:
        capture_exception()
        logger.error("Something went wrong while building Docker image for submission %d!" % submission.id)

        submission.status = Submission.SubmissionStatus.IMAGE_BUILD_FAILED
        submission.save()

        channel.basic_ack(method_frame.delivery_tag)
        # client.delete(result)

        return

    submission.status = Submission.SubmissionStatus.IMAGE_BUILD_SUCCESSFUL
    # submission.command = ' '.join(run_command)
    submission.save()

    logger.debug("Successfully created Docker image for submission %d!" % submission.id)

    # Push the image to Docker registry
    logger.debug("Pushing Docker image for submission %d..." % submission.id)
    try:
        push_image_to_registry(image_name)

        submission.status = Submission.SubmissionStatus.SUBMISSION_READY
        submission.save()

        logger.debug("Successfully pushed Docker image for submission %d!" % submission.id)
    except ChildProcessError as e:
        capture_exception()

        submission.status = Submission.SubmissionStatus.IMAGE_PUSH_FAILED
        submission.save()

        logger.error("Something went wrong while pushing Docker image for submission %d: %s!" % (submission.id, str(e)))

        return

    # Reset operator's rating for this problem, FIXME it's better to be in a post_save signal
    # Leaderboard.objects.get(
    #     problem_id=submission.problem_id
    # ).leaderboard_function.leaderboardtrueskillrank_set.update_or_create(
    #     defaults={'mu': 25.0, 'sigma': 25 / 3},
    #     owner_id=submission.owner_id
    # )
    # SimpleLeaderboard.objects.get(
    #     problem_id=submission.problem_id
    # ).simpleleaderboardrank_set.update_or_create(
    #     defaults={'precision': 0},
    #     owner_id=submission.owner_id
    # )

    channel.basic_ack(method_frame.delivery_tag)
    # client.delete(result)


if __name__ == "__main__":
    logger.info('Waiting on messages from queue "%s"...' % settings.SUBMISSION_BUILDER_QUEUE_NAME)
    client.pull(handle_new_message, settings.SUBMISSION_BUILDER_QUEUE_NAME)
