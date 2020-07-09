from enum import Enum

from django.db import models, transaction
from django.contrib.auth.models import PermissionsMixin, UnicodeUsernameValidator
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.dispatch import Signal
from django.core.exceptions import ValidationError
from django.conf import settings

from rest_framework.authtoken.models import Token
from gitlab import Gitlab

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

    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True, editable=False)

    def get_type(self):
        for t in OperatorTypes:
            if hasattr(self, t.value):
                return t

    def get_display_name(self):
        operator_type = self.get_type().value
        return "%s: %s" % (operator_type.title(), self.username)

    def __repr__(self):
        return self.get_display_name()

    def __str__(self):
        return self.username


def login(user):
    if not user.is_active:
        raise ValidationError(_("This account is inactive."), code='inactive')

    token, created = Token.objects.get_or_create(user=user)

    user.last_login = now()
    user.save()

    return token.key


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

    def _create_user(self, username, first_name, email, password, **extra_fields):
        is_test = extra_fields.pop('is_test', False)
        username = normalize_username(username)

        with transaction.atomic():
            user = self.model(username=username, first_name=first_name, **extra_fields)
            user.save()

            if settings.GITLAB_ENABLED:
                # Create Gitlab user
                gl = Gitlab.from_config(gitlab_id=settings.GITLAB_ID, config_files=[settings.GITLAB_CONFIG_PATH])
                gl_user = gl.users.create({
                    'email': email,
                    'username': username,
                    'password': password,
                    'name': user.get_full_name(),
                    'reset_password': False,
                    'projects_limit': 0,
                    'admin': False,
                    'can_create_group': False,
                    'skip_confirmation': True
                })

                if not user.is_active:
                    gl_user.deactivate()

            device = user.passworddevice_set.create(email=email)
            device.set_password(password)
            device.save()

            if not is_test:
                device.generate_challenge()

        return user

    def create_user(self, username, first_name, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        extra_fields.setdefault('is_test', False)

        return self._create_user(username, first_name, **extra_fields)

    def create_superuser(self, username, first_name, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        extra_fields.setdefault('is_test', False)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, first_name, **extra_fields)


class User(PermissionsMixin, Operator):
    first_name = models.CharField(_('first name'), max_length=30)
    last_name = models.CharField(_('last name'), max_length=150, null=True, blank=True)

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
        # Check if activation status of the user has changed
        activation_changed = False
        old_obj = self.__class__.objects.only('is_active').filter(pk=getattr(self, 'pk', None)).values().first()
        if old_obj and old_obj['is_active'] != self.is_active:
            activation_changed = True

        # Validate and save
        self.full_clean()
        super().save(**kwargs)

        # Update Gitlab user's activation status if needed
        if settings.GITLAB_ENABLED and activation_changed:
            gl = Gitlab.from_config(gitlab_id=settings.GITLAB_ID, config_files=[settings.GITLAB_CONFIG_PATH])
            gl_user = gl.users.list(username=self.username)[0]

            if self.is_active is True:
                gl_user.activate()
            else:
                gl_user.deactivate()


class Team(Operator):
    name = models.CharField(max_length=55)

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


def get_operator_model():
    """
    Returns the model which is the primary operator in the system.
    FIXME Only needed for development phase because the model might change. Delete later.
    """
    return Operator


new_user = Signal(providing_args=['user', 'username'])
