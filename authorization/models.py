from enum import Enum

from django.db import models
from django.contrib.auth.models import PermissionsMixin, UnicodeUsernameValidator
from django.utils.translation import gettext_lazy as _
from django.dispatch import Signal
from django.core.exceptions import ValidationError

from .utils import normalize_username


class OperatorTypes(Enum):
    USER = "user"
    TEAM = "team"
    PARTICIPANT = "participant"


class Operator(models.Model):
    username = models.CharField(
        _('username'),
        max_length=55,
        unique=True,
        help_text=_('Required. 55 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[UnicodeUsernameValidator()],
        error_messages={
            'unique': _("An operator with that username already exists.")
        }
    )

    def get_type(self):
        for t in OperatorTypes:
            if hasattr(self, t.value):
                return t

    def get_display_name(self):
        operator_type = self.get_type().value
        return "%s: %s" % (operator_type.title(), str(getattr(self, operator_type)))

    def __repr__(self):
        return self.get_display_name()

    def __str__(self):
        return self.__repr__()


class UserManager(models.Manager):
    def get(self, *args, **kwargs):
        if 'username' in kwargs:
            kwargs['username__iexact'] = kwargs.pop('username')
        return super().get(*args, **kwargs)

    def filter(self, *args, **kwargs):
        if 'username' in kwargs:
            kwargs['username__iexact'] = kwargs.pop('username')
        return super().filter(*args, **kwargs)

    def get_by_natural_key(self, username):
        return self.get(**{self.model.USERNAME_FIELD: username})

    def _create_user(self, username, **extra_fields):
        username = normalize_username(username)

        user = self.model(username=username, **extra_fields)
        user.save()

        return user

    def create_user(self, username, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, **extra_fields)

    def create_superuser(self, username, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, **extra_fields)


class User(PermissionsMixin, Operator):
    first_name = models.CharField(_('first name'), max_length=30)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)

    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True, editable=False)
    last_login = models.DateTimeField(_('last login'), blank=True, null=True, editable=False)

    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.')
    )
    is_active = models.BooleanField(
        _('active'),
        default=False,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        )
    )

    EMAIL_FIELD = 'id'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name']

    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def save(self, **kwargs):
        self.full_clean()
        super().save(**kwargs)


class Team(Operator):
    name = models.CharField(max_length=55)
    date_joined = models.DateTimeField(auto_now_add=True, editable=False)

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude)

        if self.name == '':
            raise ValidationError('Field "name" cannot be empty!')

    def save(self, **kwargs):
        self.full_clean()
        super().save(**kwargs)

    def __str__(self):
        return self.name


class Member(models.Model):
    user = models.ForeignKey(User, models.CASCADE)
    team = models.ForeignKey(Team, models.CASCADE)


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


def get_operator_model():
    """
    Returns the model which is the primary operator in the system.
    """
    return Operator


new_user = Signal(providing_args=['user', 'username'])
