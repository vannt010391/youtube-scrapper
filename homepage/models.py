from email.policy import default
from django.db import models

# Create your models here.
class YoutubeAPI(models.Model):
    title = models.CharField(max_length=250)
    api_key = models.CharField(max_length=250)
    create = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)
    isnable = models.BooleanField(default=True)
    note = models.TextField(blank=True)

    def __str__(self):
        return self.title



