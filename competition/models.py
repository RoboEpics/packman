from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from taggit.managers import TaggableManager

from account.models import Team
from problem.models import Problem, ProblemEnter, Run

from utils import random_path

User = get_user_model()


class Competition(models.Model):
    owner = models.ForeignKey(User, models.CASCADE, related_name='hosted_competitions')

    title = models.CharField(max_length=70)
    subtitle = models.CharField(max_length=200)

    path = models.CharField(max_length=255, unique=True, default=random_path)

    description = models.TextField()

    class ContentType(models.IntegerChoices):
        RAW_TEXT = 10, _("Raw Text")
        MARKDOWN = 20, _("Markdown")
        HTML = 30, _("HTML")
        NOTEBOOK = 40, _("Jupyter Notebook")
    content_type = models.PositiveSmallIntegerField(choices=ContentType.choices, default=ContentType.RAW_TEXT)

    rules = models.TextField(blank=True)
    prize = models.CharField(max_length=50, null=True, blank=True)

    class AccessLevel(models.IntegerChoices):
        PUBLIC = 10, _("Public")
        PRIVATE = 20, _("Private")
        LIMITED = 30, _("Limited")
    access_level = models.PositiveSmallIntegerField(choices=AccessLevel.choices, default=AccessLevel.PRIVATE)
    is_published = models.BooleanField(default=False)
    date_published = models.DateTimeField(_('date published'), null=True, blank=True)

    class ParticipationType(models.IntegerChoices):
        INDIVIDUAL = 10, _("Individual-Only")
        BOTH = 30, _("Individual and Team")
    participation_type = models.PositiveSmallIntegerField(choices=ParticipationType.choices, default=ParticipationType.BOTH)
    team_member_limit = models.PositiveIntegerField(
        null=True, blank=True,
        help_text=_(
            'Limit on the maximum number of members in each team, if the participation type is not individual-only. '
            '"null" means there is no limit!'
        )
    )
    participant_limit = models.PositiveIntegerField(
        null=True, blank=True,
        help_text=_('Limit on the maximum number of participants. "null" means there is no limit!')
    )

    register_date_start = models.DateTimeField()
    register_date_end = models.DateTimeField(null=True, blank=True)

    tags = TaggableManager(blank=True)
    category_id = models.PositiveIntegerField(null=True, blank=True, help_text=_("Category ID of Discourse for this competition."))

    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    def get_difficulty(self):
        return "simple" if self.phase_set.count() == 1 and self.phase_set.first().problems.count() == 1 else "advanced"

    def get_status(self):
        current_time = now()
        if current_time < self.register_date_start or not self.phase_set.exists():
            return 10
        elif current_time < self.phase_set.only('submission_date_start').order_by('submission_date_start').first().submission_date_start:
            return 20
        elif current_time > self.phase_set.only('submission_date_end').order_by('submission_date_end').first().submission_date_end:
            return 40
        else:
            return 30

    def get_open_phases(self):
        current_time = now()
        return self.phase_set.filter(date_start__lte=current_time, date_end__gte=current_time)

    def __str__(self):
        return "Competition: " + self.title


class CompetitionAnnouncement(models.Model):
    competition = models.ForeignKey(Competition, models.CASCADE)

    title = models.CharField(max_length=100, null=True, blank=True)
    text = models.TextField(blank=True)

    tags = TaggableManager(blank=True)

    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        ordering = ('-date_created',)


class Phase(models.Model):
    competition = models.ForeignKey(Competition, models.CASCADE)

    title = models.CharField(max_length=100)
    description = models.TextField()
    hide_until_start = models.BooleanField(default=True)

    submission_date_start = models.DateTimeField()
    submission_date_end = models.DateTimeField()
    test_date_start = models.DateTimeField(null=True, blank=True)
    test_date_end = models.DateTimeField(null=True, blank=True)
    restrict_date_start = models.DateTimeField(null=True, blank=True)
    restrict_date_end = models.DateTimeField(null=True, blank=True)

    eligible_score = models.DecimalField(max_digits=20, decimal_places=5, null=True, blank=True)

    date_created = models.DateTimeField(auto_now_add=True, editable=False)


class PhaseProblem(models.Model):
    phase = models.ForeignKey(Phase, models.CASCADE, related_name='problems')
    problem = models.OneToOneField(Problem, models.CASCADE)

    weight = models.FloatField(default=1.)
    eligible_score = models.DecimalField(max_digits=20, decimal_places=5, null=True, blank=True)


class Participant(models.Model):
    team = models.OneToOneField(Team, models.CASCADE, help_text=_("The team that is submitting to a competition."))
    competition = models.ForeignKey(Competition, models.CASCADE)

    class Meta:
        unique_together = ('team', 'competition')


class CompetitionInviteRequest(models.Model):
    competition = models.ForeignKey(Competition, models.CASCADE)
    user = models.ForeignKey(User, models.CASCADE)

    class Status(models.IntegerChoices):
        RECEIVED = 10, _("Received")
        SEEN = 20, _("Seen")
        DENIED = 30, _("Denied")
        ACCEPTED = 40, _("Accepted")
        EXPIRED = 50, _("Expired")
        CLOSED = 60, _("Closed")
    status = models.PositiveSmallIntegerField(choices=Status.choices, default=Status.RECEIVED)

    class Meta:
        unique_together = ('user', 'competition')
