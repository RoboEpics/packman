import re
import unicodedata

from django.contrib.auth.models import PermissionsMixin
from django.core import validators
from django.utils.deconstruct import deconstructible
from django.core import exceptions
from django.utils.translation import gettext_lazy as _

from taggit.managers import TaggableManager
from taggit.models import TagBase, CommonGenericTaggedItemBase

from .enums import *


@deconstructible
class ASCIIUsernameValidator(validators.RegexValidator):
    regex = r'^[\w.][\w.-]*[\w-]\Z'
    message = _(
        'Enter a valid username. This value must be longer than 2 characters and may contain only English letters, '
        'numbers, and ./-/_ characters but cannot start with a "-" or end with a ".".'
    )
    flags = re.ASCII


def validate_username_for_gitlab(value: str):
    if value.endswith('.git') or value.endswith('.atom'):
        raise exceptions.ValidationError(_('Enter a valid username. This value cannot end in ".git" or ".atom".'))


class AccountTag(TagBase):
    """
    Used for tags like "test" or "beta tester" for now.
    """

    class Meta:
        verbose_name = _("Account Tag")
        verbose_name_plural = _("Account Tags")


class TaggedAccount(CommonGenericTaggedItemBase):
    object_id = models.CharField(max_length=50, verbose_name=_("object ID"), db_index=True)
    tag = models.ForeignKey(AccountTag, models.CASCADE, related_name="%(app_label)s_%(class)s_items")


class User(PermissionsMixin):
    fusion_user_id = models.CharField(max_length=50, primary_key=True)
    gitlab_user_id = models.PositiveIntegerField(unique=True, null=True, blank=True)
    discourse_user_id = models.PositiveIntegerField(unique=True, null=True, blank=True)
    username = models.CharField(
        _('username'),
        max_length=55,
        unique=True,
        help_text=_('Required. 2 to 55 characters. Letters, digits and ./-/_ only.'),
        validators=[ASCIIUsernameValidator(), validate_username_for_gitlab],
        error_messages={
            'unique': _("A user with that username already exists!")
        }
    )
    email = models.EmailField(_('email'), unique=True)

    full_name = models.CharField(_('full name'), max_length=100)

    tags = TaggableManager(through=TaggedAccount, blank=True)

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
    is_verified = models.BooleanField(default=False, help_text=_("Designates whether this user is a verified person."))

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
        """Return the first_name."""
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

    def check_password(self, raw_password):
        return False


class Team(models.Model):
    creator = models.ForeignKey(User, models.CASCADE, related_name='teams_created')

    name = models.CharField(max_length=100, blank=True)

    individual = models.BooleanField(default=True)
    members = models.ManyToManyField(User, through='Member', related_name='teams')

    date_created = models.DateTimeField(_('date created'), auto_now_add=True, editable=False)


class Member(models.Model):
    user = models.ForeignKey(User, models.CASCADE)
    team = models.ForeignKey(Team, models.CASCADE)

    access_level = models.PositiveSmallIntegerField(choices=MemberAccessLevel.choices, default=MemberAccessLevel.MEMBER)
    status = models.PositiveSmallIntegerField(choices=MembershipStatus.choices, default=MembershipStatus.PENDING)

    date_joined = models.DateTimeField(auto_now_add=True)
