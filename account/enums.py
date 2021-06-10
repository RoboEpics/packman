from django.db import models
from django.utils.translation import gettext_lazy as _


class MemberAccessLevel(models.IntegerChoices):  # TODO discuss the different access levels
    LEADER = 10, _("Leader")
    SUBMITTER = 20, _("Submitter")
    MEMBER = 30, _("Member")


class MembershipStatus(models.IntegerChoices):
    PENDING = 10, _("Pending")
    MEMBER = 20, _("Member")
    LEFT = 30, _("Left")
