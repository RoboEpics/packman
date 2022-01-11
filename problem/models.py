from json import dumps as json_dump

from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from taggit.managers import TaggableManager
from taggit.models import TagBase, GenericTaggedItemBase

from .enums import *
from .gimulator_models import GimulatorRole
from .score_calculators import functions

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


class ScoreDefinition(models.Model):
    name = models.CharField(max_length=40, unique=True)
    description = models.TextField()


class SubmissionScoreDefinition(models.Model):
    name = models.CharField(max_length=40, unique=True)
    description = models.TextField()


class SubmissionScoreCalculator(models.Model):
    function_title = models.CharField(max_length=40, unique=True)
    description = models.TextField()


class Problem(models.Model):
    owner = models.ForeignKey(User, models.CASCADE)

    title = models.CharField(max_length=200)
    short_description = models.CharField(max_length=255)
    path = models.CharField(max_length=255, unique=True, default=random_path)

    submission_score_calculator = models.ForeignKey(SubmissionScoreCalculator, models.CASCADE, null=True, blank=True)  # "null" means no score calculation, and submission scores are probably manually set

    repository_mode = models.PositiveSmallIntegerField(choices=RepositoryMode.choices, default=RepositoryMode.ON_WITH_NOTEBOOK)

    evaluation_mode = models.PositiveSmallIntegerField(choices=EvaluationMode.choices, default=EvaluationMode.ON_AUTO)

    code_execution = models.BooleanField(default=False)

    roles = models.ManyToManyField(GimulatorRole, blank=True, related_name='as_actor')
    director_role = models.ForeignKey(GimulatorRole, models.CASCADE, related_name='as_director', null=True, blank=True)

    gimulator_tag = models.CharField(max_length=50, default='staging')
    number_of_players = models.PositiveIntegerField(null=True, blank=True)

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


class ScoreDefinedInProblem(models.Model):
    score_definition = models.ForeignKey(ScoreDefinition, models.CASCADE)
    problem = models.ForeignKey(Problem, models.CASCADE, related_name='score_definitions')

    weight = models.FloatField(default=1.)


class SubmissionScoreDefinedInProblem(models.Model):
    score_definition = models.ForeignKey(SubmissionScoreDefinition, models.CASCADE)
    problem = models.ForeignKey(Problem, models.CASCADE, related_name='submission_score_definitions')

    weight = models.FloatField(default=1.)


class ProblemCode(Code):
    problem = models.ForeignKey(Problem, models.CASCADE)

    tags = TaggableManager(through=TaggedProblemCode, blank=True)


class ProblemEnter(models.Model):
    team = models.ForeignKey(Team, models.CASCADE)
    problem = models.ForeignKey(Problem, models.CASCADE, related_name='submitters')

    code = models.OneToOneField(Code, models.CASCADE, null=True, blank=True)
    notebook_file_id = models.CharField(max_length=100, null=True, blank=True)


class Submission(models.Model):
    submitter = models.ForeignKey(User, models.CASCADE)
    problem_enter = models.ForeignKey(ProblemEnter, models.CASCADE)

    reference = models.CharField(max_length=41, null=True, blank=True)

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

    def save(self, *args, **kwargs):
        self.clean()

        problem = self.problem_enter.problem
        if not problem.code_execution:
            self.status = Submission.SubmissionStatus.SUBMISSION_READY

        super().save(*args, **kwargs)

        if not problem.code_execution and problem.output_volume_size:
            minio = clients.minio_client
            prefix = str(self.problem_enter_id) + '/'
            files = set(map(lambda f: f.object_name, minio.list_objects_v2(settings.S3_TEMP_RESULT_BUCKET_NAME, prefix=prefix)))
            for file in files:
                minio.copy_object(settings.S3_RESULT_BUCKET_NAME, "%s/%s" % (str(self.id), file.lstrip(prefix)), '%s/%s' % (settings.S3_TEMP_RESULT_BUCKET_NAME, file))

            errors = list(minio.remove_objects(settings.S3_TEMP_RESULT_BUCKET_NAME, files))
            if errors:
                raise ValidationError(list(map(lambda error: ValidationError(_("Error occurred when deleting object %(object)s"), code='delete_error', params={'object': str(error)}), errors)))

        if self.status == Submission.SubmissionStatus.WAITING_IN_QUEUE:
            if problem.code_execution:
                # Send the submission to builder queue
                clients.queue_client.push(json_dump({'submission_id': self.id}), settings.SUBMISSION_BUILDER_QUEUE_NAME)
        elif self.status == Submission.SubmissionStatus.SUBMISSION_READY and problem.evaluation_mode == EvaluationMode.ON_AUTO:
            run = Run.objects.create(owner=self.submitter, problem=problem)
            run.gatheredsubmission_set.create(submission=self)
            run.status = Run.RunStatus.READY
            run.save()

    def update_submission_score(self):
        scores = functions[self.problem_enter.problem.submission_score_calculator.function_title](self.gatheredsubmission_set.filter(run__status=Run.RunStatus.RUN_SUCCESSFUL))
        if scores is None:
            self.submissionscore_set.all().delete()
        else:
            for definition in self.problem_enter.problem.submission_score_definitions.all():
                self.submissionscore_set.update_or_create(definition=definition, defaults={'value': scores[definition.score_definition.name]})

    def generate_image_name(self):
        problem_enter = self.problem_enter
        return settings.RESULT_ONLY_IMAGE_PATH if not problem_enter.problem.code_execution else "%s:%d" % (problem_enter.code.get_git_repo_path().lower(), self.id)


class SubmissionScore(models.Model):
    submission = models.ForeignKey(Submission, models.CASCADE)
    definition = models.ForeignKey(SubmissionScoreDefinedInProblem, models.CASCADE)
    value = models.DecimalField(max_digits=20, decimal_places=5)

    class Meta:
        unique_together = ('submission', 'definition')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Type of "value" is probably "str" and we need to reload it from the database to be able to compare its value
        del self.value

        problem_enter = self.submission.problem_enter
        leaderboard = problem_enter.problem.leaderboard_set.first()  # FIXME how to choose a leaderboard?
        if leaderboard is not None:
            leaderboard_row_scores = leaderboard.leaderboardrow_set.get_or_create(problem_enter=problem_enter)[0].leaderboardscore_set
            leaderboard_score = leaderboard_row_scores.filter(score__definition=self.definition)
            if leaderboard_score.exists():
                leaderboard_score = leaderboard_score.first()
                if self.value > leaderboard_score.score.value:
                    leaderboard_score.score = self
                    leaderboard_score.save()
            else:
                leaderboard_row_scores.create(score=self)


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
            director_code = problem.problemcode_set.filter(tags__name="evaluator").first()

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
                    }
                }
            }

            clients.queue_client.push(json_dump(manifest), settings.ROOM_QUEUE_NAME)
            self.status = self.RunStatus.POD_BUILD_JOB_ENQUEUED

            super().save(*args, **kwargs)


class GatheredSubmission(models.Model):
    submission = models.ForeignKey(Submission, models.CASCADE)
    run = models.ForeignKey(Run, models.CASCADE)

    role = models.ForeignKey(GimulatorRole, models.CASCADE, null=True, blank=True)


class Score(models.Model):
    gathered_submission = models.ForeignKey(GatheredSubmission, models.CASCADE)
    definition = models.ForeignKey(ScoreDefinedInProblem, models.CASCADE)
    value = models.DecimalField(max_digits=20, decimal_places=5)

    class Meta:
        unique_together = ('gathered_submission', 'definition')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        self.gathered_submission.submission.update_submission_score()
