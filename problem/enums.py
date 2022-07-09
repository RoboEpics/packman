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


class ProblemCodeKind(models.IntegerChoices):
    EVALUATOR = 10, _('Evaluator')
    STARTER_KIT = 20, _('Starter-kit')
    OTHER = 100, _('Other')


class Runtimes(models.TextChoices):
    PYTHON = 'Python310STDINBuildPack', _("Python 3.10")
    NODE_JS = 'NodeJS18STDINBuildPack', _("NodeJS 16")
    PHP = 'PHP8STDINBuildPack', _("PHP 8")
    ERLANG = 'Erlang25STDINBuildPack', _("Erlang 25")
    CPP = 'CPP12STDINBuildPack', _("C++ 12")
    OTHER = 'other', _("Other")
