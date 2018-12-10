from .utils import *
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User
from djrichtextfield.models import RichTextField


class Post(models.Model):
    post_type = models.CharField(
        max_length=1,
        choices=POST_TYPES
    )

    title = models.CharField(max_length=200)

    content = RichTextField()

    slug = models.SlugField(
        allow_unicode=True,
        editable=False,
        unique=True,
    )

    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default='u'
    )

    feature_img = models.ImageField(
        verbose_name='Feature Image',
        upload_to=get_image_path,
        blank=True,
        null=True
    )

    user = models.ForeignKey(
        'writing.Profile',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    section = models.ForeignKey(
        'writing.Section',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} - {}".format(self.post_type, self.title)

    # override models save method for slug saving:
    def save(self, user=None, *args, **kwargs):
        if not self.id:
            self.slug = custom_slugify(value=self.title.lower())

            backup_img = self.feature_img
            self.feature_img = None
            super(Post, self).save()  # saving post without img field
            self.feature_img = backup_img

        if user:
            self.user = user
        super(Post, self).save()  # saving the post finally

    def is_img_exists(self):
        return os.path.isfile(self.feature_img.path)

    # making that function object's boolean value is true, so the admin panel's can show this as a boolean
    is_img_exists.boolean = True

    def get_categories(self):
        return self.categorize_set.all()  # <model_name lowercase><underscore>set: somemodelname_set

    # def get_absolute_url(self):
    #     return reverse(
    #         'main_app:each_post',
    #         args=[
    #             str(self.id),
    #             str(self.slug)
    #         ]
    #     )


class Category(models.Model):
    name = models.CharField(max_length=25)

    slug = models.SlugField(
        allow_unicode=True,
        editable=False
    )

    post = models.ManyToManyField(
        'writing.Post',
        through='Categorize',
        through_fields=(
            'category',
            'post',
        ),
    )

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    # override models save method for slug saving:
    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = custom_slugify(value=self.name.lower())
        super(Category, self).save()  # saving the slug automatically

    # def get_absolute_url(self):
    #     return reverse(
    #         'main_app:each_category',
    #         args=[
    #             str(self.slug)
    #         ]
    #     )


class Categorize(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE
    )

    def __str__(self):
        data = {'category': self.category, 'post': self.post}
        return "{category} : {post}".format(**data)

    class Meta:
        verbose_name = "Post Category Relation"


class Section(models.Model):
    name = models.CharField(max_length=25)

    # description = models.CharField(max_length=1000)

    icon = models.TextField()  # will save svg code

    slug = models.SlugField(
        allow_unicode=True,
        editable=False
    )

    # post = models.ManyToManyField(
    #     'writing.Post',
    #     through='Sectionize',
    #     through_fields=(
    #         'section',
    #         'post',
    #     ),
    # )

    def __str__(self):
        return self.name

    # override models save method for slug saving:
    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = custom_slugify(value=self.name.lower())
        super(Section, self).save()  # saving the slug automatically

    # def get_absolute_url(self):
    #     return reverse(
    #         'main_app:each_category',
    #         args=[
    #             str(self.slug)
    #         ]
    #     )


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    bio = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
    )

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
