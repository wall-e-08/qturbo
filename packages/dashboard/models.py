from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from djrichtextfield.models import RichTextField
from .utils import get_image_path


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
        return "{} - {}".format(self.get_position_display(), self.url_text)


class GeneralTopic(models.Model):
    # TODO: need restrictions in saving ArrayField
    top_quote_heading = models.TextField(max_length=500)
    top_quote_sub_heading = models.TextField(max_length=500)
    top_img = models.ImageField(
        verbose_name='Top Image',
        upload_to=get_image_path
    )
    top_text = RichTextField()

    service_heading = models.TextField(
        verbose_name="Service Heading",
        max_length=300,
    )
    service_sub_heading = models.TextField(
        verbose_name="Service Sub Heading",
        max_length=300,
    )
    service_items = models.TextField()  # ["page_ItemIcon_id", "description"]
    service_img = models.ImageField(
        verbose_name='Service Image',
        upload_to=get_image_path
    )

    statistics = models.TextField()  # ["number of sell", "what is sold"]

    review_heading = models.TextField(max_length=500)
    review_items = ArrayField(
        RichTextField(),
        size=2,
    )
    review_bg = models.ImageField(
        verbose_name="Review Background Image",
        upload_to=get_image_path,
    )

    faq_heading = models.TextField(max_length=300)
    faq_img = models.ImageField(
        verbose_name="FAQ Image",
        upload_to=get_image_path,
    )
    faqs = ArrayField(
        ArrayField(
            models.CharField(max_length=500, blank=True),
            size=2,
        ),
    )

    quote_heading = models.TextField(
        verbose_name="All page quote Heading",
        max_length=300,
    )
    quote_bg = models.ImageField(
        verbose_name="Get Quote Background Image",
        upload_to=get_image_path,
    )

    footer_left = models.TextField()
    footer_middle = models.TextField()
    copyright_text = models.CharField(max_length=200)
    social_links = ArrayField(
        ArrayField(
            models.CharField(max_length=200, blank=True),
            size=2,
        ),
    )

    last_edited_time = models.DateTimeField(
        verbose_name="Last edited on",
        editable=False,
        blank=True, null=True,
    )

    def save(self, *args, **kwargs):
        if GeneralTopic.objects.exists() and not self.id:
            # Only one instance allowed
            raise ValidationError('Only one GeneralTopics instance allowed! Edit the remaining one, if you need to change.')

        self.last_edited_time = timezone.now()  # On save, update timestamps
        return super(GeneralTopic, self).save(*args, **kwargs)

    @staticmethod
    def get_the_instance():
        try:
            return GeneralTopic.objects.all()[0]
        except IndexError:
            print("GeneralTopic is not created yet.")
        return None
