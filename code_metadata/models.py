from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from account.models import Operator

User = get_user_model()


class Code(models.Model):
    owner = models.ForeignKey(Operator, models.CASCADE)

    project_id = models.PositiveIntegerField()

    date_created = models.DateTimeField(_("date created"), auto_now_add=True, editable=False)

    def get_git_path(self):
        return settings.GITLAB_CLIENT.projects.get(self.project_id).path_with_namespace
