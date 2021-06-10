from django.db import models
from django.conf import settings
from django.apps import apps
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

    class ContentType(models.IntegerChoices):
        RAW_TEXT = 10, _("Raw Text")
        MARKDOWN = 20, _("Markdown")
        HTML = 30, _("HTML")
        NOTEBOOK = 40, _("Jupyter Notebook")
    content_type = models.PositiveSmallIntegerField(choices=ContentType.choices, default=ContentType.RAW_TEXT)  # TODO find a better way

    class AccessLevel(models.IntegerChoices):
        PUBLIC = 10, _("Public")
        PRIVATE = 20, _("Private")
        LIMITED = 30, _("Limited")
    access_level = models.PositiveSmallIntegerField(choices=AccessLevel.choices, default=AccessLevel.PRIVATE)

    upvotes = models.ManyToManyField(User, related_name='upvoted_datasets', blank=True)

    tags = TaggableManager(blank=True)

    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Data(models.Model):
    dataset = models.ForeignKey(Dataset, models.CASCADE, related_name='versions')

    version = models.CharField(max_length=20)

    description = models.TextField(null=True, blank=True)
    license = models.TextField(null=True, blank=True)

    class DataStatus(models.IntegerChoices):
        UPLOADING = 10, _("Uploading to temporary storage")
        TRANSFER = 20, _("Transferring to main storage")
        FINALIZING = 30, _("Finalizing")
        READY = 40, _("Ready")

    status = models.PositiveSmallIntegerField(choices=DataStatus.choices, default=DataStatus.TRANSFER)

    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        ordering = ('-date_created',)
        unique_together = ('dataset', 'version')


class File(models.Model):
    data = models.ForeignKey(Data, models.CASCADE)
    file_name = models.CharField(max_length=255)
    file_id = models.CharField(max_length=100)

    def get_url(self):
        return apps.get_app_config("dataset").minio_client.presigned_get_object(settings.S3_TEMP_DATASET_BUCKET_NAME, "%d/%s" % (self.data.dataset_id, self.file_name))
        # return apps.get_app_config("dataset").google_drive_client.files().get(fileId=self.file_id, fields='webContentLink').execute()['webContentLink']

    def __str__(self):
        return self.file_name
