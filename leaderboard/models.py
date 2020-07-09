from django.db import models

from authorization.models import Operator


class Leaderboard(models.Model):
    problem = models.ForeignKey('problem.Problem', models.CASCADE)
    title = models.CharField(max_length=50)


class TrueSkillLeaderboard(Leaderboard):  # TODO migrate this to MongoDB
    pass


class TrueSkillLeaderboardRank(models.Model):  # TODO migrate this to MongoDB
    leaderboard = models.ForeignKey(TrueSkillLeaderboard, models.CASCADE)
    owner = models.ForeignKey(Operator, models.CASCADE)

    mu = models.FloatField(default=25.)
    sigma = models.FloatField(default=25/3)


class SimpleLeaderboard(Leaderboard):
    pass


class SimpleLeaderboardRank(models.Model):
    leaderboard = models.ForeignKey(SimpleLeaderboard, models.CASCADE)
    owner = models.ForeignKey(Operator, models.CASCADE)

    precision = models.FloatField(default=0.)
