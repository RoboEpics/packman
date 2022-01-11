from yaml import dump

from django.db import models


class Resource(models.Model):
    cpu = models.FloatField(default=1.)
    memory = models.PositiveIntegerField(default=256)
    ephemeral = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"cpu: {self.cpu}, memory: {self.memory}, ephemeral: {self.ephemeral}"


class GimulatorMethod(models.Model):
    name = models.CharField(max_length=20, primary_key=True)

    def __str__(self):
        return self.name


class GimulatorKey(models.Model):
    type = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    namespace = models.CharField(max_length=50)

    def __str__(self):
        return ', '.join((self.type, self.name, self.namespace))

    def to_dict(self) -> dict:
        return {'type': self.type, 'name': self.name, 'namespace': self.namespace}


class GimulatorRule(models.Model):
    key = models.ForeignKey(GimulatorKey, models.CASCADE)
    methods = models.ManyToManyField(GimulatorMethod)

    def __str__(self):
        return f"{{{str(self.key)}}}: [{', '.join(str(method) for method in self.methods.all())}]"

    def to_dict(self) -> dict:
        return {'key': self.key.to_dict(), 'methods': list(self.methods.values_list('name', flat=True))}


class GimulatorRole(models.Model):
    name = models.CharField(max_length=30)
    rules = models.ManyToManyField(GimulatorRule)
    resource_limit = models.ForeignKey(Resource, models.CASCADE, null=True, blank=True, related_name='as_limit')
    resource_request = models.ForeignKey(Resource, models.CASCADE, null=True, blank=True, related_name='as_request')

    def __str__(self):
        return self.name


def roles_to_yaml(director: GimulatorRole, roles: list) -> str:
    return dump({'director': [rule.to_dict() for rule in director.rules.all()] if director else [],
                 'actors': {role.name: [rule.to_dict() for rule in role.rules.all()] for role in roles}})
