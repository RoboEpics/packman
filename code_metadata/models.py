from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Code(models.Model):
    project_id = models.PositiveIntegerField()

    date_created = models.DateTimeField(_("date created"), auto_now_add=True, editable=False)

    def get_git_repo_path(self):
        return settings.GITLAB_CLIENT.projects.get(self.project_id).path_with_namespace

    def get_git_repo_url(self):
        return '/'.join((settings.GIT_URL, self.get_git_repo_path())) + '.git'

    def get_gitlab_project_url(self):
        return '/'.join((settings.GITLAB_URL, self.get_git_repo_path()))

    def get_project(self):
        return settings.GITLAB_CLIENT.projects.get(self.project_id)

    def change_project_name(self, name):
        settings.GITLAB_CLIENT.projects.update(self.project_id, {'name': name})

    def add_member(self, user):
        self.member_set.create(user=user)

    def delete_member(self, user):
        self.member_set.get(user=user).delete()

    def delete(self, **kwargs):
        if settings.GITLAB_ENABLED:
            settings.GITLAB_CLIENT.projects.delete(self.project_id)
        return super().delete(**kwargs)


class Member(models.Model):
    user = models.ForeignKey(User, models.CASCADE, related_name='repositories')
    code = models.ForeignKey(Code, models.CASCADE)
