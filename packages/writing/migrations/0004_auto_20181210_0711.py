# Generated by Django 2.1.3 on 2018-12-10 07:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('writing', '0003_auto_20181210_0653'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='category',
            name='slug',
            field=models.SlugField(allow_unicode=True, editable=False, max_length=200, unique=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='slug',
            field=models.SlugField(allow_unicode=True, editable=False, max_length=1000, unique=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='title',
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name='section',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='section',
            name='slug',
            field=models.SlugField(allow_unicode=True, editable=False, max_length=200, unique=True),
        ),
    ]
