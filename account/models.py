from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import PermissionsMixin, UnicodeUsernameValidator, UserManager
from django.contrib.auth.base_user import AbstractBaseUser


class User(AbstractBaseUser, PermissionsMixin):
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

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'

    objects = UserManager()

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


class Team(models.Model):
    creator = models.ForeignKey(User, models.CASCADE)

    name = models.CharField(max_length=70)


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


class Operator(models.Model):
    owner = models.ForeignKey(User, models.CASCADE)
    team = models.ForeignKey(Team, models.SET_NULL, null=True, blank=True)
