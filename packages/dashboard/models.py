from django.db import models


class Menu(models.Model):
    parent_menu = models.ForeignKey(
        'Menu',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    url = models.CharField(max_length=300)

    url_text = models.CharField(max_length=300)

    position = models.CharField(
        max_length=3,
        choices=(
            ('top', 'Header'),
            ('btm', 'Footer'),
        ),
    )

    def __str__(self):
        return "Menu - {}".format(self.url_text)



