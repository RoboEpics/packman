from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from gitlab import const

User = get_user_model()


class CodeManager(models.Manager):
    gitlab_client = settings.GITLAB_CLIENT

    def _create_repo(self, namespace, path):
        gl = self.gitlab_client

        gl_group = gl.groups.get(namespace)
        gl_project = gl.projects.create({'path': path, 'namespace_id': gl_group.id, 'builds_access_level': 'disabled'})

        return gl_project

    def create(self, namespace, path, members, **kwargs):
        gl_project = self._create_repo(namespace, path)

        instance = super().create(project_id=gl_project.id, **kwargs)

        for user in members:
            Member.objects.create(code=instance, user=user)

        return instance


class MemberManager(models.Manager):
    def create(self, code, user):
        code.get_project().members.create({'user_id': user.gitlab_user_id, 'access_level': const.DEVELOPER_ACCESS})
        return super().create(code=code, user=user)


class Code(models.Model):
    project_id = models.PositiveIntegerField()

    date_created = models.DateTimeField(_("date created"), auto_now_add=True, editable=False)

    objects = CodeManager()

    def get_git_repo_path(self):
        return settings.GITLAB_CLIENT.projects.get(self.project_id).path_with_namespace

    def get_git_repo_url(self):
        return '/'.join((settings.GIT_URL, self.get_git_repo_path())) + '.git'

    def get_gitlab_project_url(self):
        return '/'.join((settings.GITLAB_URL, self.get_git_repo_path()))

    def get_project(self):
        return settings.GITLAB_CLIENT.projects.get(self.project_id)


class Member(models.Model):
    user = models.ForeignKey(User, models.CASCADE, related_name='repositories')
    code = models.ForeignKey(Code, models.CASCADE)

    objects = MemberManager()
