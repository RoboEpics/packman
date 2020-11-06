from django.db import models

from account.models import Operator


class Leaderboard(models.Model):
    problem = models.ForeignKey('problem.Problem', models.CASCADE)
    title = models.CharField(max_length=100)


class SimpleLeaderboard(Leaderboard):
    pass


class SimpleLeaderboardRank(models.Model):
    leaderboard = models.ForeignKey(SimpleLeaderboard, models.CASCADE)
    owner = models.ForeignKey(Operator, models.CASCADE)

    precision = models.FloatField(default=0.)
