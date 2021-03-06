# Generated by Django 2.1.3 on 2018-12-10 06:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('writing', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='slug',
            field=models.SlugField(allow_unicode=True, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name='section',
            name='slug',
            field=models.SlugField(allow_unicode=True, editable=False, unique=True),
        ),
    ]
