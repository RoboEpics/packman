from django.db import models
from django.contrib.auth import get_user_model
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
    path = models.CharField(max_length=255)

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

    selected = ExclusiveBooleanField(on=('submitter', 'problem'), default=False)

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
        unique_together = ('submitter', 'problem', 'reference')

    def generate_image_name(self):
        return "%s:%d" % (self.problem_enter.get_git_path().lower(), self.id)


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
