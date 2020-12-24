import unicodedata

from django.db import models
from django.contrib.auth.models import PermissionsMixin, UnicodeUsernameValidator, UserManager
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from taggit.managers import TaggableManager
from taggit.models import TagBase, CommonGenericTaggedItemBase


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
    gitlab_user_id = models.IntegerField(unique=True, null=True, blank=True)
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

    full_name = models.CharField(_('full name'), max_length=100)
    profile_picture = models.ImageField(upload_to='profile', default='profile/no_avatar.png')

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

    objects = UserManager()

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

    def get_gitlab_user(self):
        return settings.GITLAB_CLIENT.users.get(self.gitlab_user_id)

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
    def create(self, name, image, creator, members=None):
        if members is None:
            members = []

        team = super().create(name=name, image=image, creator=creator)

        team.member_set.create(user=creator, status=Member.MembershipStatus.MEMBER)
        for member in members:
            if creator.trusted_by.filter(truster=member).exists():
                team.member_set.create(user=member, status=Member.MembershipStatus.MEMBER)
            else:
                team.inviterequest_set.create(user=member)

        return team


class Team(models.Model):
    creator = models.ForeignKey(User, models.CASCADE)

    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='profile', default='team_profile/no_avatar.png')

    members = models.ManyToManyField(User, through='Member', related_name='teams')

    date_created = models.DateTimeField(_('date created'), auto_now_add=True, editable=False)

    objects = TeamManager()


class Member(models.Model):
    user = models.ForeignKey(User, models.CASCADE)
    team = models.ForeignKey(Team, models.CASCADE)

    class AccessLevel(models.IntegerChoices):  # TODO discuss the different access levels
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
        EXPIRED = 50, _("Expired")
        CLOSED = 60, _("Closed")

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


class TeamEventHistory(models.Model):
    team = models.ForeignKey(Team, models.CASCADE)

    text = models.CharField(max_length=255)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        ordering = ('-date_created',)
