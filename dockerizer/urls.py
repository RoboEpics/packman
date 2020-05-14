from subprocess import Popen, PIPE
from json import loads

from django.conf import settings
from django.utils.module_loading import import_string

from problem.models import Submission

# Initialize message queue client
client = import_string(settings.QUEUE_CLIENT)(settings.QUEUE_CLIENT_API_HOST)


def create_docker_image(gitlab_repo, commit_hash):
    # Create Docker image from git repository using jupyter-repo2docker
    image_name = '/'.join((settings.DOCKER_REGISTRY_HOST, gitlab_repo))
    Popen((
        'jupyter-repo2docker', '--no-run',
        '--image-name', image_name,
        '--ref', commit_hash,
        '/'.join((settings.GITLAB_HOST, gitlab_repo))
    ), stdout=PIPE, stderr=PIPE)

    return image_name


def push_image_to_registry(image_name):
    password = Popen(('cat', settings.DOCKER_REGISTRY_PASSWORD_FILE), stdout=PIPE)
    Popen(('sudo', 'docker', 'login', '--username', settings.DOCKER_REGISTRY_USERNAME, '--password-stdin', settings.DOCKER_REGISTRY_HOST), stdin=password.stdout, stdout=PIPE, stderr=PIPE)
    Popen(('sudo', 'docker', 'push', image_name), stdout=PIPE, stderr=PIPE)


def handle_new_message(channel, method, properties, body):
    request = loads(body)
    submission = Submission.objects.get(id=request['submission_id'])

    # Create Docker image from Gitlab repository
    image_name = create_docker_image(submission.generate_image_name(), submission.reference)

    # Push the image to Docker registry
    push_image_to_registry(image_name)


print('Waiting on messages from queue "%s"...' % settings.QUEUE_NAME)
client.pull(handle_new_message, settings.QUEUE_NAME)

urlpatterns = []
