from enum import Enum
import unicodedata

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import PermissionsMixin, UnicodeUsernameValidator


class OperatorTypes(Enum):
    TEAM = "team"
    PARTICIPANT = "participant"


class Operator(models.Model):
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True, editable=False)

    def get_type(self):
        for t in OperatorTypes:
            if hasattr(self, t.value):
                return t


class User(PermissionsMixin):
    fusion_user_id = models.CharField(max_length=200, primary_key=True)
    username = models.CharField(
        _('username'),
        max_length=55,
        unique=True,
        help_text=_('Required. 55 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[UnicodeUsernameValidator()],
        error_messages={
            'unique': _("A user with that username already exists.")
        }
    )
    email = models.EmailField(_('email'), unique=True)

    full_name = models.CharField(_('full name'), max_length=150)
    profile_picture = models.ImageField(upload_to='profile', default='profile/no_avatar.png')

    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True, editable=False)
    last_login = models.DateTimeField(_('last login'), blank=True, null=True, editable=False)

    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into the admin site.')
    )
    is_active = models.BooleanField(
        _('active'),
        default=False,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        )
    )

    REQUIRED_FIELDS = []

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_short_name(self):
        """Return the short name for the user."""
        return self.full_name

    def get_full_name(self):
        """
        Return the first_name.
        """
        return self.get_short_name()

    def get_username(self):
        """Return the username for this User."""
        return getattr(self, self.USERNAME_FIELD)

    def clean(self):
        setattr(self, self.USERNAME_FIELD, self.normalize_username(self.get_username()))

    def natural_key(self):
        return self.get_username(),

    @property
    def is_anonymous(self):
        """
        Always return False. This is a way of comparing User objects to
        anonymous users.
        """
        return False

    @property
    def is_authenticated(self):
        """
        Always return True. This is a way to tell if the user has been
        authenticated in templates.
        """
        return True

    @classmethod
    def get_email_field_name(cls):
        try:
            return cls.EMAIL_FIELD
        except AttributeError:
            return 'email'

    @classmethod
    def normalize_username(cls, username):
        return unicodedata.normalize('NFKC', username) if isinstance(username, str) else username

    def __str__(self):
        return "User: " + self.get_username()


class Trust(models.Model):
    truster = models.ForeignKey(User, models.CASCADE, related_name='trusting')
    trusted = models.ForeignKey(User, models.CASCADE, related_name='trusted_by')

    class Meta:
        unique_together = ('truster', 'trusted')


class TeamManager(models.Manager):
    def create(self, name, creator, members):
        team = super().create(name=name, creator=creator)
        team.member_set.create(user=creator, status=Member.MembershipStatus.MEMBER)

        for member in members:
            user = User.objects.get(username=member)
            if creator.trusted_by.filter(truster=user).exists():
                team.member_set.create(user=user, status=Member.MembershipStatus.MEMBER)
            else:
                team.inviterequest_set.create(user=user)

        return team


class Team(Operator):
    creator = models.ForeignKey(User, models.CASCADE)

    name = models.CharField(max_length=70)

    objects = TeamManager()


class Member(models.Model):
    user = models.ForeignKey(User, models.CASCADE)
    team = models.ForeignKey(Team, models.CASCADE)

    class AccessLevel(models.IntegerChoices):
        LEADER = 10, _("Leader")
        SUBMITTER = 20, _("Submitter")
        MEMBER = 30, _("Member")

    access_level = models.PositiveSmallIntegerField(choices=AccessLevel.choices, default=AccessLevel.MEMBER)

    data_joined = models.DateTimeField(auto_now_add=True)

    class MembershipStatus(models.IntegerChoices):
        PENDING = 10, _("Pending")
        MEMBER = 20, _("Member")
        LEFT = 30, _("Left")

    status = models.PositiveSmallIntegerField(choices=MembershipStatus.choices, default=MembershipStatus.PENDING)


class InviteRequest(models.Model):
    team = models.ForeignKey(Team, models.CASCADE)
    user = models.ForeignKey(User, models.CASCADE)

    class InviteRequestStatus(models.IntegerChoices):
        RECEIVED = 10, _("Received")
        SEEN = 20, _("Seen")
        DENIED = 30, _("Denied")
        ACCEPTED = 40, _("Accepted")

    status = models.PositiveSmallIntegerField(choices=InviteRequestStatus.choices, default=InviteRequestStatus.RECEIVED)


class JoinRequest(models.Model):
    user = models.ForeignKey(User, models.CASCADE)
    team = models.ForeignKey(Team, models.CASCADE)

    class JoinRequestStatus(models.IntegerChoices):
        RECEIVED = 10, _("Received")
        SEEN = 20, _("Seen")
        DENIED = 30, _("Denied")
        ACCEPTED = 40, _("Accepted")

    status = models.PositiveSmallIntegerField(choices=JoinRequestStatus.choices, default=JoinRequestStatus.RECEIVED)
