from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from taggit.managers import TaggableManager

from account.models import Team
from problem.models import Problem, Run

User = get_user_model()


class Competition(models.Model):
    owner = models.ForeignKey(User, models.CASCADE, related_name='hosted_competitions')

    title = models.CharField(max_length=70)
    subtitle = models.CharField(max_length=100)
    description = models.TextField()
    rules = models.TextField()

    thumbnail = models.ImageField(null=True, blank=True)
    cover_image = models.ImageField(null=True, blank=True)

    is_public = models.BooleanField(default=False)
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

    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    def get_difficulty(self):
        return "simple" if self.phase_set.count() == 1 and self.phase_set.first().problems.count() == 1 else "advanced"

    def get_open_phases(self, type=None):
        current_time = now()
        type_filter = {'type': type} if type is not None else {}
        return self.phase_set.filter(date_start__lte=current_time, date_end__gte=current_time, **type_filter)

    def __str__(self):
        return "Competition: " + self.title


class CompetitionAnnouncement(models.Model):
    competition = models.ForeignKey(Competition, models.CASCADE)

    text = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        ordering = ('-date_created',)


class Phase(models.Model):  # TODO LeaderBoard
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

    date_created = models.DateTimeField(auto_now_add=True, editable=False)


class PhaseProblem(models.Model):
    phase = models.ForeignKey(Phase, models.CASCADE, related_name='problems')
    problem = models.OneToOneField(Problem, models.CASCADE)

    weight = models.FloatField(default=1.)


class Participant(models.Model):
    team = models.OneToOneField(Team, models.CASCADE, help_text=_("The team that is submitting to a competition."))
    competition = models.ForeignKey(Competition, models.CASCADE)

    class Meta:
        unique_together = ('team', 'competition')
