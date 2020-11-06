from django.db import models
from django.utils.translation import gettext_lazy as _

from taggit.managers import TaggableManager

from account.models import Operator, User


class Dataset(models.Model):
    owner = models.ForeignKey(Operator, models.CASCADE, related_name='datasets')

    title = models.CharField(max_length=70, unique=True)
    subtitle = models.CharField(max_length=100, null=True, blank=True)

    cover_image = models.ImageField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    is_public = models.BooleanField(default=False, editable=False)
    upvotes = models.ManyToManyField(User, related_name='upvoted_datasets')

    tags = TaggableManager()

    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Data(models.Model):
    dataset = models.ForeignKey(Dataset, models.CASCADE, related_name='versions')

    previous_version = models.OneToOneField('self', models.SET_NULL, null=True, blank=True)
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
        ordering = ('date_created',)
        unique_together = ('dataset', 'version')


class File(models.Model):
    data = models.ForeignKey(Data, models.CASCADE)
    file_id = models.CharField(max_length=100)
