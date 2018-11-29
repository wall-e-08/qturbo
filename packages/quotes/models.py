from django.db import models


class Leads(models.Model):
    zip_code = models.CharField(max_length=5)

    dob = models.DateField()

    gender = models.CharField(max_length=1)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}_{}".format(self.zip_code, self.gender)
