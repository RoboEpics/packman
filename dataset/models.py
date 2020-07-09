from django.db import models

from taggit.managers import TaggableManager

from authorization.models import get_operator_model


class Dataset(models.Model):
    owner = models.ForeignKey(get_operator_model(), models.CASCADE, related_name='datasets')

    title = models.CharField(max_length=70, unique=True)
    subtitle = models.CharField(max_length=100, null=True, blank=True)
    cover_image = models.ImageField(null=True, blank=True)

    tags = TaggableManager()

    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.full_clean()
        return super().save(force_insert, force_update, using, update_fields)


class Data(models.Model):
    dataset = models.ForeignKey(Dataset, models.CASCADE, related_name='versions')

    previous_version = models.OneToOneField('self', models.SET_NULL, null=True, blank=True)

    version = models.CharField(max_length=20)
    description = models.TextField(null=True, blank=True)
    license = models.TextField(null=True, blank=True)

    directory_name = models.CharField(max_length=300)

    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        ordering = ('date_created',)
        unique_together = ('dataset', 'version')
