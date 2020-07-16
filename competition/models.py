from django.db import models
from django.utils.translation import gettext_lazy as _

from authorization.models import get_operator_model
from problem.models import Problem, Run

Operator = get_operator_model()


class Competition(models.Model):
    owner = models.ForeignKey(Operator, models.CASCADE, related_name='hosted_competitions')

    title = models.CharField(max_length=100)
    description = models.TextField()

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
    daily_submission_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Limit on the maximum number of submission per day by each participant. "null" means there is no limit!')
    )
    is_public = models.BooleanField(default=False)

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
    owner = models.ForeignKey(Operator, models.CASCADE, related_name='participations', help_text=_("The User or Team that is submitting to a competition with this Operator."))
    competition = models.ForeignKey(Competition, models.CASCADE)

    date_participated = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        unique_together = ('owner', 'competition')

    def save(self, **kwargs):  # FIXME participant shouldn't have a username
        self.username = "Participant-" + self.owner.username
        super().save(**kwargs)

    def __str__(self):
        return self.username
