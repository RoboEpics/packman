from django.db import models
from django.utils.translation import gettext_lazy as _

from account.models import Operator
from problem.models import Problem, Run


class Competition(models.Model):
    owner = models.ForeignKey(Operator, models.CASCADE, related_name='hosted_competitions')

    title = models.CharField(max_length=100)
    description = models.TextField()
    is_public = models.BooleanField(default=False)

    class ParticipationType(models.IntegerChoices):
        INDIVIDUAL = 10, _("Individual-Only")
        TEAM = 20, _("Team-Only")
        BOTH = 30, _("Individual and Team")

    participation_type = models.PositiveSmallIntegerField(choices=ParticipationType.choices, default=ParticipationType.BOTH)
    team_member_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_(
            'Limit on the maximum number of members in each team, if the participation type is not individual-only. '
            '"null" means there is no limit!'
        )
    )
    participant_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Limit on the maximum number of participants. "null" means there is no limit!')
    )

    date_created = models.DateTimeField(auto_now_add=True, editable=False)


class Phase(models.Model):
    competition = models.ForeignKey(Competition, models.CASCADE)
    problems = models.ManyToManyField(Problem)
    runs = models.ManyToManyField(Run, blank=True)

    description = models.TextField()
    hide_until_start = models.BooleanField(default=True)

    date_start = models.DateTimeField()
    date_end = models.DateTimeField()
    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    class PhaseTypes(models.IntegerChoices):
        REGISTER = 10, _("Register")
        SUBMISSION = 20, _("Submission")
        TEST = 30, _("Test")
        RESTRICT = 40, _("Restrict")

    type = models.PositiveSmallIntegerField(choices=PhaseTypes.choices)


class Participant(Operator):
    operator = models.ForeignKey(Operator, models.CASCADE, related_name='participations', help_text=_("The Team that is submitting to a competition with this Operator."))
    competition = models.ForeignKey(Competition, models.CASCADE)

    class Meta:
        unique_together = ('operator', 'competition')
