from json import dumps as json_dump

from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from taggit.managers import TaggableManager
from taggit.models import TagBase, GenericTaggedItemBase

from .enums import *
from .gimulator_models import GimulatorRole

from account.models import Team
from code_metadata.models import Code
from dataset.models import Data

from utils import random_path, clients

User = get_user_model()


class ProblemCodeTag(TagBase):
    class Meta:
        verbose_name = _("Problem Code Tag")
        verbose_name_plural = _("Problem Code Tags")


class TaggedProblemCode(GenericTaggedItemBase):
    tag = models.ForeignKey(ProblemCodeTag, models.CASCADE, related_name="%(app_label)s_%(class)s_items")


class Problem(models.Model):
    owner = models.ForeignKey(User, models.CASCADE)

    title = models.CharField(max_length=200)
    short_description = models.CharField(max_length=255)
    path = models.CharField(max_length=255, unique=True, default=random_path)

    repository_mode = models.PositiveSmallIntegerField(choices=RepositoryMode.choices, default=RepositoryMode.ON_WITH_NOTEBOOK)

    evaluation_mode = models.PositiveSmallIntegerField(choices=EvaluationMode.choices, default=EvaluationMode.ON_AUTO)

    code_execution = models.BooleanField(default=False)

    roles = models.ManyToManyField(GimulatorRole, blank=True, related_name='as_actor')
    director_role = models.ForeignKey(GimulatorRole, models.CASCADE, related_name='as_director', null=True, blank=True)

    gimulator_tag = models.CharField(max_length=50, default='staging')
    number_of_players = models.PositiveIntegerField(null=True, blank=True)
    timeout = models.PositiveIntegerField(null=True, blank=True)
    terminate_on_actor_failure = models.BooleanField(default=True)

    datasets = models.ManyToManyField(Data, blank=True)

    submission_file_name = models.CharField(max_length=255, null=True, blank=True)
    output_volume_size = models.PositiveBigIntegerField(null=True, blank=True)

    default_resource_cpu_limit = models.FloatField(default=1.)
    default_resource_memory_limit = models.PositiveBigIntegerField(default=256)
    default_resource_ephemeral_limit = models.PositiveBigIntegerField(default=0)

    gimulator_resource_cpu_limit = models.FloatField(default=1.)
    gimulator_resource_memory_limit = models.PositiveBigIntegerField(default=256)
    gimulator_resource_ephemeral_limit = models.PositiveBigIntegerField(default=0)

    is_public = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    date_published = models.DateTimeField(_('date published'), null=True, blank=True)

    gitlab_group_id = models.PositiveIntegerField(null=True, blank=True)

    tags = TaggableManager(blank=True)


class ProblemCode(Code):
    problem = models.ForeignKey(Problem, models.CASCADE)

    kind = models.PositiveSmallIntegerField(choices=ProblemCodeKind.choices, default=ProblemCodeKind.OTHER)


class ProblemEnter(models.Model):
    team = models.ForeignKey(Team, models.CASCADE)
    problem = models.ForeignKey(Problem, models.CASCADE, related_name='submitters')

    code = models.OneToOneField(Code, models.CASCADE, null=True, blank=True)
    notebook_file_id = models.CharField(max_length=100, null=True, blank=True)


class Submission(models.Model):
    submitter = models.ForeignKey(User, models.CASCADE)
    problem_enter = models.ForeignKey(ProblemEnter, models.CASCADE)

    reference = models.CharField(max_length=41, null=True, blank=True)
    runtime = models.CharField(max_length=50, choices=Runtimes.choices, null=True, blank=True)

    class SubmissionStatus(models.IntegerChoices):
        WAITING_IN_QUEUE = 10, _("Waiting In Queue")

        IMAGE_BUILD_JOB_ENQUEUED = 20, _("Image Build Job Enqueued")
        IMAGE_BUILD_STARTED = 30, _("Image Build Started")

        IMAGE_BUILD_FAILED = 40, _("Image Build Failed")
        IMAGE_BUILD_SUCCESSFUL = 50, _("Image Build Successful")

        IMAGE_PUSH_FAILED = 60, _("Image Push Failed")

        SUBMISSION_READY = 100, _("Submission Ready")
    status = models.PositiveSmallIntegerField(choices=SubmissionStatus.choices, default=SubmissionStatus.WAITING_IN_QUEUE)

    runs = models.ManyToManyField('Run', through='GatheredSubmission')  # A shortcut for simplicity

    def clean(self):
        if self.problem_enter.problem.repository_mode != RepositoryMode.OFF and Submission.objects.filter(problem_enter=self.problem_enter, reference=self.reference).exclude(pk=self.pk).exists():
            raise ValidationError(_("You cannot submit with the same commit reference you have submitted before!"), code='invalid')

    def save(self, skip_run=False, *args, **kwargs):
        self.clean()

        problem = self.problem_enter.problem
        if not problem.code_execution:
            self.status = Submission.SubmissionStatus.SUBMISSION_READY

        super().save(*args, **kwargs)

        if not skip_run and self.status == Submission.SubmissionStatus.SUBMISSION_READY and problem.evaluation_mode == EvaluationMode.ON_AUTO:
            run = Run.objects.create(owner=self.submitter, problem=problem)
            run.gatheredsubmission_set.create(submission=self, role=problem.roles.first())
            run.status = Run.RunStatus.READY
            run.save()

    def generate_image_name(self):
        problem_enter = self.problem_enter
        return settings.RESULT_ONLY_IMAGE_PATH if not problem_enter.problem.code_execution else "%s:%d" % (problem_enter.code.get_git_repo_path().lower(), self.id)


class Run(models.Model):
    owner = models.ForeignKey(User, models.CASCADE)
    problem = models.ForeignKey(Problem, models.CASCADE)  # A shortcut for efficiency

    class RunStatus(models.IntegerChoices):
        PREPARING = 10, _("Preparing")
        READY = 20, _("Ready To Be Run")

        POD_BUILD_JOB_ENQUEUED = 30, _("Pod Build Job Enqueued")
        POD_BUILD_STARTED = 40, _("Pod Build Started")

        POD_BUILD_FAILED = 50, _("Pod Build Failed")
        POD_BUILD_SUCCESSFUL = 60, _("Pod Build Successful")

        WAITING_IN_QUEUE_TO_RUN = 70, _("Waiting In Queue To Run")
        RUN_INITIATED = 80, _("Run Initiated")

        RUN_FAILED = 90, _("Run Failed")
        RUN_SUCCESSFUL = 100, _("Run Successful")
    status = models.PositiveSmallIntegerField(choices=RunStatus.choices, default=RunStatus.PREPARING)

    date_created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.status == self.RunStatus.READY:
            problem = self.problem

            director_role = problem.director_role
            director_code = problem.problemcode_set.filter(kind=ProblemCodeKind.EVALUATOR).first()

            manifest = {
                'apiVersion': 'hub.roboepics.com/v1',
                'kind': 'Room',
                'metadata': {
                    'name': 'room-%d' % self.id,
                    'namespace': settings.HUB_NAMESPACE
                },
                'spec': {
                    'id': str(self.id),
                    'problemID': str(problem.id),

                    'director': {
                        'name': '-'.join((str(director_code.id), str(self.id))),
                        'image': '/'.join((
                            settings.DOCKER_REGISTRY_HOST,
                            "%s:%d" % (director_code.get_git_repo_path().lower(), director_code.id)
                        )),
                        'resources': {
                            'limits': {
                                'cpu': str(director_role.resource_limit.cpu),
                                'memory': str(director_role.resource_limit.memory) + 'Mi',
                                'ephemeral-storage': str(director_role.resource_limit.ephemeral) + 'Mi'
                            } if director_role.resource_limit else {},
                            'requests': {
                                'cpu': str(director_role.resource_request.cpu),
                                'memory': str(director_role.resource_request.memory) + 'Mi',
                                'ephemeral-storage': str(director_role.resource_request.ephemeral) + 'Mi'
                            } if director_role.resource_request else {}
                        } if director_role else {}
                    },
                    'actors': [
                        {
                            'name': str(gathered_submission.id),
                            'image': '/'.join((
                                settings.DOCKER_REGISTRY_HOST,
                                gathered_submission.submission.generate_image_name()
                            )),
                            'role': gathered_submission.role.name if gathered_submission.role else 'agent',
                            'envs': [
                                {'name': 'S3_ENDPOINT_URL', 'value': settings.S3_ENDPOINT_URL.split('//')[1]},
                                {'name': 'S3_ACCESS_KEY_ID', 'value': settings.S3_ACCESS_KEY_ID},
                                {'name': 'S3_SECRET_ACCESS_KEY', 'value': settings.S3_SECRET_ACCESS_KEY},
                                {'name': 'S3_RESULT_BUCKET_NAME', 'value': settings.S3_RESULT_BUCKET_NAME},
                                {'name': 'S3_PATH_PREFIX', 'value': str(gathered_submission.submission_id) + '/'}
                            ] if problem.code_execution is False else [],
                            'resources': {
                                'limits': {
                                    'cpu': str(gathered_submission.role.resource_limit.cpu),
                                    'memory': str(gathered_submission.role.resource_limit.memory) + 'Mi',
                                    'ephemeral-storage': str(gathered_submission.role.resource_limit.ephemeral) + 'Mi'
                                } if gathered_submission.role.resource_limit else {},
                                'requests': {
                                    'cpu': str(gathered_submission.role.resource_request.cpu),
                                    'memory': str(gathered_submission.role.resource_request.memory) + 'Mi',
                                    'ephemeral-storage': str(gathered_submission.role.resource_request.ephemeral) + 'Mi'
                                } if gathered_submission.role.resource_request else {}
                            } if gathered_submission.role else {}
                        } for gathered_submission in self.gatheredsubmission_set.all()
                    ],
                    'metrico': {
                        'enabled': True,
                        'name': str(self.id),
                        'image': 'xerac/metrico:staging'
                    },
                    'timeout': problem.timeout,
                    'terminateOnActorFailure': problem.terminate_on_actor_failure
                }
            }

            clients.queue_client.push(json_dump(manifest), '%s-%d' % (settings.ROOM_QUEUE_NAME_PREFIX, problem.id))

            self.status = self.RunStatus.POD_BUILD_JOB_ENQUEUED

            super().save(*args, **kwargs)


class GatheredSubmission(models.Model):
    submission = models.ForeignKey(Submission, models.CASCADE)
    run = models.ForeignKey(Run, models.CASCADE)

    role = models.ForeignKey(GimulatorRole, models.CASCADE, null=True, blank=True)
