from .utils import (POST_TYPES, STATUS_CHOICES, get_image_path, custom_slugify)
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User
from djrichtextfield.models import RichTextField


class Post(models.Model):
    title = models.CharField(max_length=500)

    content = RichTextField()

    slug = models.SlugField(
        max_length=1000,
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
        return self.title

    # override models save method for slug saving:
    def save(self, user=None, *args, **kwargs):
        if not self.id:
            slug = custom_slugify(value=self.title.lower())
            slug_exists = True
            counter = 1
            self.slug = slug
            while slug_exists:
                try:
                    slug_exits = Post.objects.get(slug=slug)
                    if slug_exits:
                        slug = self.slug + '-' + str(counter)
                        counter += 1
                except Post.DoesNotExist:
                    self.slug = slug
                    break

        if user:
            self.user = user
        super(Post, self).save()  # saving the slug

    # def is_img_exists(self):
    #     return os.path.isfile(self.feature_img.path)
    # 
    # # making that function object's boolean value is true, so the admin panel's can show this as a boolean
    # is_img_exists.boolean = True

    def get_absolute_url(self):
        return reverse(
            'blog:each_blog',
            args=[
                str(self.slug)
            ]
        )


class Article(Post):
    post_type = models.CharField(
        max_length=1,
        default='a',
        editable=False
    )


class Blog(Post):
    post_type = models.CharField(
        max_length=1,
        default='b',
        editable=False
    )

    def get_categories(self):
        return self.categorize_set.all()  # <model_name lowercase><underscore>set: somemodelname_set


class Category(models.Model):
    name = models.CharField(max_length=100)

    slug = models.SlugField(
        max_length=200,
        allow_unicode=True,
        editable=False,
        unique=True,
    )

    blog = models.ManyToManyField(
        'writing.Blog',
        through='Categorize',
        through_fields=(
            'category',
            'blog',
        ),
    )

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            'blog:categorized_blog',
            args=[str(self.slug),]
        )

    def blogs_count_under_this(self):
        return len(Blog.objects.filter(categorize__category=self))

    # override models save method for slug saving:
    def save(self, *args, **kwargs):
        if not self.id:
            slug = custom_slugify(value=self.name.lower())
            slug_exists = True
            counter = 1
            self.slug = slug
            while slug_exists:
                try:
                    slug_exits = Category.objects.get(slug=slug)
                    if slug_exits:
                        slug = self.slug + '-' + str(counter)
                        counter += 1
                except Category.DoesNotExist:
                    self.slug = slug
                    break
        super(Category, self).save(*args, **kwargs)  # saving the slug


class Categorize(models.Model):
    blog = models.ForeignKey(
        Blog,
        on_delete=models.CASCADE
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE
    )

    def __str__(self):
        data = {'category': self.category, 'post': self.blog}
        return "{category} : {post}".format(**data)

    class Meta:
        verbose_name = "Blog Category Relation"


class Section(models.Model):
    name = models.CharField(max_length=100)

    post_type = models.CharField(
        max_length=1,
        choices=POST_TYPES,
    )

    description = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
    )

    icon = models.TextField()  # will save svg code

    slug = models.SlugField(
        max_length=200,
        allow_unicode=True,
        editable=False,
        unique=True
    )

    def __str__(self):
        return self.name

    # override models save method for slug saving:
    def save(self, *args, **kwargs):
        if not self.id:
            slug = custom_slugify(value=self.name.lower())
            slug_exists = True
            counter = 1
            self.slug = slug
            while slug_exists:
                try:
                    slug_exits = Section.objects.get(slug=slug)
                    if slug_exits:
                        slug = self.slug + '-' + str(counter)
                        counter += 1
                except Section.DoesNotExist:
                    self.slug = slug
                    break
        super(Section, self).save(*args, **kwargs)  # saving the slug

    def get_absolute_url_article(self):
        return reverse(
            'article:sectionized_article',
            args=[str(self.slug),]
        )

    def get_absolute_url_blog(self):
        return reverse(
            'blog:sectionized_blog',
            args=[str(self.slug),]
        )

    def blogs_count_under_this(self):
        return len(Blog.objects.filter(section=self))

    def articles_count_under_this(self):
        return len(Article.objects.filter(section=self))


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
