from django.db import models
from django.utils.translation import gettext_lazy as _


class RepositoryMode(models.IntegerChoices):
    OFF = 10, _("Off")
    ON = 20, _("On")
    ON_WITH_NOTEBOOK = 30, _("On, With Notebook")


class EvaluationMode(models.IntegerChoices):
    OFF = 10, _("Off")
    ON = 20, _("On")
    ON_AUTO = 30, _("On, Auto-Evaluate")


class Runtimes(models.TextChoices):
    PYTHON = "Python310STDINBuildPack", _('Python 3.10')
    NODE_JS = "NodeJS16STDINBuildPack", _('NodeJS 16')
    PHP = "PHP8STDINBuildPack", _('PHP 8')
