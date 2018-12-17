from django.db import models
from django.shortcuts import reverse
from writing.utils import custom_slugify
from djrichtextfield.models import RichTextField


class Page(models.Model):
    title = models.CharField(max_length=200)
    content = RichTextField()

    slug = models.SlugField(
        max_length=1000,
        allow_unicode=True,
        editable=False,
        unique=True,
    )

    template_file = models.CharField(
        max_length=100,
    )

    page_content = []

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
            args=[str(self.slug),]
        )


class Homepage(Page):
    # page_content = Page.page_content + []
    pass

