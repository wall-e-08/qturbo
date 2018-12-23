from django.db import models
from django.shortcuts import reverse
from writing.utils import custom_slugify
from djrichtextfield.models import RichTextField
from writing.utils import STATUS_CHOICES
from .utils import get_img_path


class Page(models.Model):
    title = models.CharField(max_length=200)
    content = RichTextField(
        blank=True,
        null=True,
    )

    slug = models.SlugField(
        max_length=1000,
        allow_unicode=True,
        editable=False,
        unique=True,
    )

    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default='p'
    )

    template_file = models.CharField(
        max_length=100,
    )

    create_time = models.DateTimeField(auto_now_add=True)

    # override models save method for slug saving:
    def save(self, user=None, *args, **kwargs):
        if not self.id:
            slug = custom_slugify(value=self.title.lower())
            slug_exists = True
            counter = 1
            self.slug = slug
            while slug_exists:
                try:
                    slug_exits = Page.objects.get(slug=slug)
                    if slug_exits:
                        slug = self.slug + '-' + str(counter)
                        counter += 1
                except Page.DoesNotExist:
                    self.slug = slug
                    break

        super(Page, self).save()  # saving the slug

    def get_absolute_url(self):
        return reverse(
            'slugified_page',
            args=[str(self.slug), ]
        )


class Homepage(Page):
    # page_content = Page.page_content + []
    pass


class ItemList(models.Model):
    page = models.ForeignKey(
        'Page',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    icon = models.ForeignKey(
        'ItemIcon',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    content = RichTextField(
        blank=True,
        null=True,
    )

    url = models.CharField(
        max_length=200,
        blank=True,
        null=True,
    )


class ItemIcon(models.Model):
    title = models.CharField(max_length=100)

    svg_icon = models.TextField(
        verbose_name='SVG Code',
        blank=True,
        null=True,
    )

    img_icon = models.ImageField(
        verbose_name='Image File',
        upload_to=get_img_path,
        blank=True,
        null=True,
    )

    icon_type = models.CharField(
        choices=(
            ('svg', 'SVG Code'),
            ('img', 'Image file'),
        ),
        max_length=3,
    )

    def __str__(self):
        return self.title


class ItemTwoColumn(models.Model):
    """items with 2 columns: image + text"""
    title = models.CharField(
        max_length=200,
        blank=True,
        null=True,
    )

    img = models.ImageField(
        verbose_name='Single Image',
        upload_to=get_img_path,
        blank=True,
        null=True
    )

    content = RichTextField()

    url = models.CharField(
        max_length=200,
        blank=True,
        null=True,
    )

    url_text = models.CharField(
        max_length=200,
        blank=True,
        null=True,
    )


class ItemGuide(models.Model):
    url = models.CharField(
        max_length=200,
    )

    url_text = models.CharField(
        max_length=200,
    )
