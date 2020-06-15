from django.db import models

from authorization.models import Operator


class LeaderboardFunction(models.Model):  # TODO migrate this to MongoDB
    title = models.CharField(max_length=50)
    file_path = models.TextField()


class LeaderboardTrueSkillRank(models.Model):  # TODO migrate this to MongoDB
    function = models.ForeignKey(LeaderboardFunction, models.CASCADE)
    owner = models.ForeignKey(Operator, models.CASCADE)

    mu = models.FloatField(default=25.)
    sigma = models.FloatField(default=25/3)


class Leaderboard(models.Model):
    problem = models.ForeignKey('problem.Problem', models.CASCADE)
    leaderboard_function = models.ForeignKey(LeaderboardFunction, models.CASCADE)
