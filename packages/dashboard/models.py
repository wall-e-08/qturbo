from django.db import models
from djrichtextfield.models import RichTextField


class Page(models.Model):
    title = models.CharField(max_length=200)
    content = RichTextField()
    create_time = models.DateTimeField(auto_now_add=True)

