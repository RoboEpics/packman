from django.conf import settings
from django.apps import apps

from .enums import *

from code_metadata.models import Code


def initialize_problem_group(problem):
    gl = settings.GITLAB_CLIENT

    problem.gitlab_group_id = group_id = gl.groups.create({'name': problem.title, 'path': problem.path}).id
    problem.save()

    if problem.repository_mode != RepositoryMode.OFF:
        gl.groups.create({'name': 'submissions', 'path': 'submissions', 'parent_id': group_id, 'auto_devops_enabled': False})

    if problem.evaluation_mode != EvaluationMode.OFF:
        utilities_group = gl.groups.create({'name': 'utilities', 'path': 'utilities', 'parent_id': group_id, 'auto_devops_enabled': False})

        obj = apps.get_model('problem', 'ProblemCode').objects.create(
            members=[problem.owner], namespace=utilities_group.full_path, path='evaluator', problem=problem)
        obj.tags.add('evaluator')


class ProblemManager(models.Manager):
    def create(self, **kwargs):
        problem = super().create(**kwargs)

        # Create an empty Overview text
        problem.problemtext_set.create(title='Overview', order=1)

        # Create Gitlab groups and evaluator repository
        initialize_problem_group(problem)

        return problem


class ProblemEnterManager(models.Manager):
    def create(self, team, problem):
        return super().create(
            code=Code.objects.create(
                namespace='/'.join((problem.path, 'submissions')), name=team.name if team.name else team.creator.full_name,
                path=str(team.id), members=team.members.all()
            ) if problem.repository_mode != RepositoryMode.OFF else None,
            problem=problem, team=team
        )
