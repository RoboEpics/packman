from django.db import models
from django.utils.translation import gettext_lazy as _

from taggit.managers import TaggableManager

from account.models import User
from utils import random_path


class Dataset(models.Model):
    owner = models.ForeignKey(User, models.CASCADE, related_name='datasets')

    title = models.CharField(max_length=70, unique=True)
    subtitle = models.CharField(max_length=100, null=True, blank=True)

    path = models.CharField(max_length=255, unique=True, default=random_path)

    cover_image = models.ImageField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class AccessLevel(models.IntegerChoices):
        PUBLIC = 10, _("Public")
        PRIVATE = 20, _("Private")
        LIMITED = 30, _("Limited")
    access_level = models.PositiveSmallIntegerField(choices=AccessLevel.choices, default=AccessLevel.PRIVATE)

    upvotes = models.ManyToManyField(User, related_name='upvoted_datasets', blank=True)

    tags = TaggableManager(blank=True)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Data(models.Model):
    dataset = models.ForeignKey(Dataset, models.CASCADE, related_name='versions')

    version = models.CharField(max_length=20)

    description = models.TextField(null=True, blank=True)

    class DataStatus(models.IntegerChoices):
        UPLOADING = 10, _("Uploading to temporary storage")
        TRANSFER = 20, _("Transferring to main storage")
        FINALIZING = 30, _("Finalizing")
        READY = 40, _("Ready")
    status = models.PositiveSmallIntegerField(choices=DataStatus.choices, default=DataStatus.TRANSFER)

    class Meta:
        ordering = ('-date_created',)
        unique_together = ('dataset', 'version')

    @property
    def temp_bucket_path(self):
        return str(self.dataset_id)

    @property
    def is_public(self):
        return self.dataset.access_level == Dataset.AccessLevel.PUBLIC

    @property
    def pvc_name(self):
        return 'dataset-%d-version-%d' % (self.dataset_id, self.id)
