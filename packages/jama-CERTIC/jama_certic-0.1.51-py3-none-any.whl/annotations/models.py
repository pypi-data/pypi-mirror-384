from django.contrib.auth.models import User
from django.db import models
from resources.models import Resource


class Annotation(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    data = models.JSONField("JSON data")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    public = models.BooleanField(default=False)
