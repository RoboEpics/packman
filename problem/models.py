from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from slugify import slugify

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
    config_file = models.FileField(upload_to=settings.PROBLEM_CONFIG_PATH)

    date_created = models.DateTimeField(auto_now_add=True)

    is_published = models.BooleanField(default=False, editable=False)
    date_published = models.DateTimeField(null=True, blank=True, editable=False)

    def get_slug(self):
        return slugify(self.title)

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude)
        if self.owner.get_type() not in [OperatorTypes.USER, OperatorTypes.TEAM]:
            raise ValidationError('Owner type must be either "User" or "Team"')

    def save(self, **kwargs):
        self.full_clean()
        super().save(**kwargs)


class Submission(models.Model):
    owner = models.ForeignKey(Operator, models.CASCADE)
    problem = models.ForeignKey(Problem, models.CASCADE)

    reference = models.CharField(max_length=41)
    command = models.CharField(max_length=255, null=True, blank=True)

    class SubmissionStatus(models.IntegerChoices):
        WAITING_IN_QUEUE = 10, _("Waiting In Queue")

        IMAGE_BUILD_JOB_ENQUEUED = 20, _("Image Build Job Enqueued")
        IMAGE_BUILD_STARTED = 30, _("Image Build Started")

        IMAGE_BUILD_FAILED = 40, _("Image Build Failed")
        IMAGE_BUILD_SUCCESSFUL = 50, _("Image Build Successful")

    status = models.PositiveSmallIntegerField(choices=SubmissionStatus.choices, default=SubmissionStatus.WAITING_IN_QUEUE)

    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    def generate_git_repo_path(self):
        return "%s/%s" % (self.problem.get_slug(), self.owner.username)

    def generate_image_name(self):
        return "%s:%d" % (self.generate_git_repo_path().lower(), self.id)


class Run(models.Model):
    owner = models.ForeignKey(Operator, models.CASCADE)
    problem = models.ForeignKey(Problem, models.CASCADE)
    score_definitions = models.ManyToManyField(ScoreDefinition, blank=True)

    class RunStatus(models.IntegerChoices):
        WAITING_IN_QUEUE = 10, _("Waiting In Queue")

        POD_BUILD_JOB_ENQUEUED = 20, _("Pod Build Job Enqueued")
        POD_BUILD_STARTED = 30, _("Pod Build Started")

        POD_BUILD_FAILED = 40, _("Pod Build Failed")
        POD_BUILD_SUCCESSFUL = 50, _("Pod Build Successful")

        WAITING_IN_QUEUE_FOR_EVALUATION = 60, _("Waiting In Queue To Run")
        EVALUATION_INITIATED = 70, _("Run Initiated")

        EVALUATION_FAILED = 80, _("Run Failed")
        EVALUATION_SUCCESSFUL = 90, _("Run Successful")

    status = models.PositiveSmallIntegerField(choices=RunStatus.choices, default=RunStatus.WAITING_IN_QUEUE)

    date_created = models.DateTimeField(auto_now_add=True, editable=False)


class GatheredSubmission(models.Model):
    submission = models.ForeignKey(Submission, models.CASCADE)
    run = models.ForeignKey(Run, models.CASCADE)


class Score(models.Model):
    gathered_submission = models.ForeignKey(GatheredSubmission, models.CASCADE)
    definition = models.ForeignKey(ScoreDefinition, models.CASCADE)
    value = models.BigIntegerField()

    class Meta:
        unique_together = ('gathered_submission', 'definition')
