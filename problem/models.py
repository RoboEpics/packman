from yaml import safe_load, dump
from gitlab import const

from django.db import models
from django.apps import apps
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.translation import gettext_lazy as _
from django.core import exceptions

from taggit.managers import TaggableManager
from slugify import slugify
from exclusivebooleanfield import ExclusiveBooleanField

from authorization.models import get_operator_model, OperatorTypes
from dataset.models import Dataset

Operator = get_operator_model()


class ScoreDefinition(models.Model):
    name = models.CharField(max_length=40, unique=True)
    description = models.TextField()


class Problem(models.Model):
    owner = models.ForeignKey(Operator, models.CASCADE)

    title = models.CharField(max_length=100)
    description = models.TextField()

    datasets = models.ManyToManyField(Dataset, blank=True)
    config_file = models.FileField()

    date_created = models.DateTimeField(auto_now_add=True)

    is_public = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False, editable=False)
    date_published = models.DateTimeField(null=True, blank=True, editable=False)

    tags = TaggableManager()

    def get_slug(self):
        return "-".join((slugify(self.title), str(self.id)))

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude)
        if self.owner.get_type() not in [OperatorTypes.USER, OperatorTypes.TEAM]:
            raise exceptions.ValidationError('Owner type must be either "User" or "Team"')

    def save(self, **kwargs):
        self.full_clean()
        super().save(**kwargs)


class ProblemEnter(models.Model):
    operator = models.ForeignKey(Operator, models.CASCADE, related_name='problems_entered')
    problem = models.ForeignKey(Problem, models.CASCADE, related_name='submitters')

    date_entered = models.DateTimeField(auto_now_add=True)

    def get_gitlab_repo_url(self):
        if not settings.GITLAB_ENABLED:
            return ''
        return "/".join((settings.GITLAB_URL, self.problem.get_slug(), self.operator.username))

    def save(self, **kwargs):
        super().save(**kwargs)
        problem = self.problem
        operator = self.operator

        if settings.GITLAB_ENABLED:
            # Create Gitlab repository in the problem group for the operator
            gl = settings.GITLAB_CLIENT
            gl_group = gl.groups.get(problem.get_slug())
            gl_project = gl.projects.create({
                'name': operator.username,
                'namespace_id': gl_group.id
            })
            if operator.get_type() == OperatorTypes.PARTICIPANT:
                operator = operator.participant.owner

            if operator.get_type() == OperatorTypes.TEAM:
                members = operator.team.member_set.all()
                for member in members:
                    gl_user = gl.users.list(username=member.user.username)[0]
                    gl_project.members.create({'user_id': gl_user.id, 'access_level': const.DEVELOPER_ACCESS})
            else:
                gl_user = gl.users.list(username=operator.username)[0]
                gl_project.members.create({'user_id': gl_user.id, 'access_level': const.DEVELOPER_ACCESS})


class Submission(models.Model):
    owner = models.ForeignKey(Operator, models.CASCADE)
    problem = models.ForeignKey(Problem, models.CASCADE)

    reference = models.CharField(max_length=41)
    command = models.CharField(max_length=255, null=True, blank=True)

    selected = ExclusiveBooleanField(on=('owner', 'problem'), default=False)

    class SubmissionStatus(models.IntegerChoices):
        WAITING_IN_QUEUE = 10, _("Waiting In Queue")

        IMAGE_BUILD_JOB_ENQUEUED = 20, _("Image Build Job Enqueued")
        IMAGE_BUILD_STARTED = 30, _("Image Build Started")

        IMAGE_BUILD_FAILED = 40, _("Image Build Failed")
        IMAGE_BUILD_SUCCESSFUL = 50, _("Image Build Successful")

        IMAGE_PUSH_FAILED = 60, _("Image Push Failed")
        IMAGE_READY = 70, _("Image Ready")

    status = models.PositiveSmallIntegerField(choices=SubmissionStatus.choices, default=SubmissionStatus.WAITING_IN_QUEUE)

    runs = models.ManyToManyField('Run', through='GatheredSubmission')

    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        ordering = ("-date_created",)

    def generate_git_repo_path(self):
        return "%s/%s" % (self.problem.get_slug(), self.owner.username)

    def generate_image_name(self):
        return "%s:%d" % (self.generate_git_repo_path().lower(), self.id)


class Run(models.Model):
    owner = models.ForeignKey(Operator, models.CASCADE)
    problem = models.ForeignKey(Problem, models.CASCADE)  # FIXME is this needed?
    score_definitions = models.ManyToManyField(ScoreDefinition, blank=True)

    class RunStatus(models.IntegerChoices):
        PREPARING = 10, _("Preparing")
        READY = 15, _("Ready To Be Run")

        POD_BUILD_JOB_ENQUEUED = 20, _("Pod Build Job Enqueued")
        POD_BUILD_STARTED = 30, _("Pod Build Started")

        POD_BUILD_FAILED = 40, _("Pod Build Failed")
        POD_BUILD_SUCCESSFUL = 50, _("Pod Build Successful")

        WAITING_IN_QUEUE_TO_RUN = 60, _("Waiting In Queue To Run")
        RUN_INITIATED = 70, _("Run Initiated")

        RUN_FAILED = 80, _("Run Failed")
        RUN_SUCCESSFUL = 90, _("Run Successful")

    status = models.PositiveSmallIntegerField(choices=RunStatus.choices, default=RunStatus.PREPARING)

    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        ordering = ("-date_created",)

    def save(self, **kwargs):
        super().save(**kwargs)

        if self.status == self.RunStatus.READY:
            with default_storage.open(self.problem.config_file.name) as file:
                problem_config = safe_load(file.read())
            resource_limits = problem_config['resource-limits']

            # manifest = {
            #     'apiVersion': 'hub.xerac.cloud/v1',
            #     'kind': 'Room',
            #     'metadata': {
            #         'name': 'room-%d' % self.id,
            #         'namespace': 'hub-system'
            #     },
            #     'spec': {
            #         'backoff-limit': 2,
            #         'active-dead-line-seconds': 30,
            #         'id': self.id,
            #         'sketch': 'gimulator-roles',
            #         'actors': [
            #             {
            #                 'name': str(gathered_submission.submission.owner),
            #                 'role': 'agent',
            #                 'image': '/'.join((settings.DOCKER_REGISTRY_HOST,
            #                                    gathered_submission.submission.generate_image_name())),
            #                 'command': gathered_submission.submission.command,
            #                 'id': gathered_submission.id,
            #                 'resources': {
            #                     'requests': resource_limits,
            #                     'limits': resource_limits
            #                 }
            #             } for gathered_submission in self.gatheredsubmission_set.all()
            #         ] + [
            #             {
            #                 'name': 'judge-team',
            #                 'role': 'judge',
            #                 'image': component['image'],
            #                 'command': component['command'],
            #                 'type': 'master',
            #                 'id': self.problem_id,
            #                 'resources': {
            #                     'requests': resource_limits,
            #                     'limits': resource_limits
            #                 }
            #             } for name, component in problem_config['components'].items()
            #         ],
            #         'config-maps': [
            #             {
            #                 'name': 'gimulator-roles',
            #                 'data': dump(problem_config['roles'])
            #             }
            #         ]
            #     }
            # }

            gathered_submission = self.gatheredsubmission_set.first()
            manifest = {
                'apiVersion': 'hub.xerac.cloud/v1',
                'kind': 'ML',
                'metadata': {
                    'name': 'ml-%d' % self.id,
                    'namespace': 'hub-system'
                },
                'spec': {
                    'run-id': self.id,
                    'submission-id': gathered_submission.id,

                    'evaluator-image': problem_config['components']['judge']['image'],
                    'submission-image': '/'.join((settings.DOCKER_REGISTRY_HOST, gathered_submission.submission.generate_image_name())),

                    'data-persist-volume-claim-name': 'diginext-train-data',
                    'evaluation-persist-volume-claim-name': 'diginext-evaluation-data',

                    'cpu-resource-request': resource_limits['cpu'],
                    'memory-resource-request': resource_limits['memory'],
                    'ephemeral-resource-request': resource_limits['ephemeral'],

                    'cpu-resource-limit': resource_limits['cpu'],
                    'memory-resource-limit': resource_limits['memory'],
                    'ephemeral-resource-limit': resource_limits['ephemeral'],

                    'backoff-limit': 0
                }
            }

            apps.get_app_config("problem").kubernetes.create_namespaced_custom_object(
                group="hub.xerac.cloud",
                version="v1",
                namespace="hub-system",
                plural="mls",
                body=manifest,
            )

            self.status = self.RunStatus.POD_BUILD_JOB_ENQUEUED
            super().save(**kwargs)


class GatheredSubmission(models.Model):
    submission = models.ForeignKey(Submission, models.CASCADE)
    run = models.ForeignKey(Run, models.CASCADE)


class Score(models.Model):
    gathered_submission = models.ForeignKey(GatheredSubmission, models.CASCADE)
    definition = models.ForeignKey(ScoreDefinition, models.CASCADE)
    value = models.DecimalField(max_digits=20, decimal_places=5)

    class Meta:
        unique_together = ('gathered_submission', 'definition')
