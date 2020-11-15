from json import dumps

from django.db import models
from django.contrib.auth import get_user_model
from django.apps import apps
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from taggit.managers import TaggableManager
from taggit.models import TagBase, GenericTaggedItemBase

from exclusivebooleanfield import ExclusiveBooleanField

from account.models import Operator
from code_metadata.models import Code
from dataset.models import Data

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


class Problem(models.Model):
    owner = models.ForeignKey(Operator, models.CASCADE)

    title = models.CharField(max_length=200)
    short_description = models.CharField(max_length=255)
    path = models.CharField(max_length=255, unique=True)

    thumbnail = models.ImageField(null=True, blank=True)
    cover_image = models.ImageField(null=True, blank=True)

    gimulator_tag = models.CharField(max_length=40, null=True, blank=True)
    number_of_players = models.PositiveIntegerField(null=True, blank=True)

    datasets = models.ManyToManyField(Data)

    output_volume_size = models.PositiveIntegerField(null=True, blank=True)
    resource_cpu_limit = models.FloatField(default=1.)
    resource_memory_limit = models.PositiveIntegerField(default=256)
    resource_ephemeral_limit = models.PositiveIntegerField(default=0)

    is_public = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    date_published = models.DateTimeField(_('date published'), null=True, blank=True)

    date_created = models.DateTimeField(_('date created'), auto_now_add=True, editable=False)

    tags = TaggableManager()

    class Meta:
        ordering = ("-date_created",)


class ProblemText(models.Model):
    problem = models.ForeignKey(Problem, models.CASCADE)

    title = models.CharField(max_length=30)
    text = models.TextField()

    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ('order',)


class ProblemCode(Code):
    problem = models.ForeignKey(Problem, models.CASCADE)

    tags = TaggableManager(through=TaggedProblemCode)


class ProblemEnter(Code):
    problem = models.ForeignKey(Problem, models.CASCADE, related_name='submitters')

    notebook_file_id = models.CharField(max_length=100, null=True, blank=True)


class Submission(models.Model):
    submitter = models.ForeignKey(User, models.CASCADE)
    problem_enter = models.ForeignKey(ProblemEnter, models.CASCADE)
    problem = models.ForeignKey(Problem, models.CASCADE)  # A shortcut for efficiency

    reference = models.CharField(max_length=41)

    selected = ExclusiveBooleanField(on=('problem_enter', 'problem'), default=False)

    class SubmissionStatus(models.IntegerChoices):
        WAITING_IN_QUEUE = 10, _("Waiting In Queue")

        IMAGE_BUILD_JOB_ENQUEUED = 20, _("Image Build Job Enqueued")
        IMAGE_BUILD_STARTED = 30, _("Image Build Started")

        IMAGE_BUILD_FAILED = 40, _("Image Build Failed")
        IMAGE_BUILD_SUCCESSFUL = 50, _("Image Build Successful")

        IMAGE_PUSH_FAILED = 60, _("Image Push Failed")

        SUBMISSION_READY = 100, _("Submission Ready")

    status = models.PositiveSmallIntegerField(choices=SubmissionStatus.choices, default=SubmissionStatus.WAITING_IN_QUEUE)

    runs = models.ManyToManyField('Run', through='GatheredSubmission')

    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        ordering = ("-date_created",)
        unique_together = ('submitter', 'problem', 'reference')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.status == Submission.SubmissionStatus.WAITING_IN_QUEUE and self.problem.gimulator_tag is not None:
            apps.get_app_config("problem").queue.push(dumps({'submission_id': self.id}), settings.SUBMISSION_BUILDER_QUEUE_NAME)
        elif self.status == Submission.SubmissionStatus.SUBMISSION_READY and self.problem.number_of_players is None:
            run = Run.objects.create(owner=self.problem_enter.owner, problem=self.problem)
            run.gatheredsubmission_set.create(submission=self)
            run.score_definitions.add(1)
            run.status = Run.RunStatus.READY
            run.save()

    def generate_image_name(self):
        if self.problem.gimulator_tag is None:
            return "roboepics/competitions/roboepics-result-only-submission:latest"
        return "%s:%d" % (self.problem_enter.get_git_repo_path().lower(), self.id)


class Run(models.Model):
    owner = models.ForeignKey(Operator, models.CASCADE)
    problem = models.ForeignKey(Problem, models.CASCADE)  # A shortcut for efficiency
    score_definitions = models.ManyToManyField(ScoreDefinition, blank=True)

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

    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        ordering = ("-date_created",)

    def save(self, **kwargs):
        super().save(**kwargs)

        if self.status == self.RunStatus.READY:
            director_code = self.problem.problemcode_set.filter(tags__name="evaluator").first()
            manifest = {
                'apiVersion': 'hub.roboepics.com/v1',
                'kind': 'Room',
                'metadata': {
                    'name': 'room-%d' % self.id,
                    'namespace': 'hub-system'
                },
                'spec': {
                    'id': str(self.id),
                    'problemID': str(self.problem_id),

                    'director': {
                        'name': '-'.join((str(director_code.id), str(self.id))),
                        'image': '/'.join((
                            settings.DOCKER_REGISTRY_HOST,
                            "%s:%d" % (director_code.get_git_repo_path().lower(), director_code.id)
                        ))
                    },
                    'actors': [
                        {
                            'name': str(gathered_submission.id),
                            'image': '/'.join((
                                settings.DOCKER_REGISTRY_HOST,
                                gathered_submission.submission.generate_image_name()
                            )),
                            'role': gathered_submission.role
                        } for gathered_submission in self.gatheredsubmission_set.all()
                    ]
                }
            }

            apps.get_app_config("problem").queue.push(dumps(manifest), settings.ROOM_QUEUE_NAME)

            super().save(**kwargs)


class GatheredSubmission(models.Model):
    submission = models.ForeignKey(Submission, models.CASCADE)
    role = models.CharField(max_length=50, default='agent')
    run = models.ForeignKey(Run, models.CASCADE)


class Score(models.Model):
    gathered_submission = models.ForeignKey(GatheredSubmission, models.CASCADE)
    definition = models.ForeignKey(ScoreDefinition, models.CASCADE)
    value = models.DecimalField(max_digits=20, decimal_places=5)

    class Meta:
        unique_together = ('gathered_submission', 'definition')
