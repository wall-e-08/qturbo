# Generated by Django 2.1.3 on 2019-01-02 06:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('distinct_pages', '0010_auto_20190101_0622'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='itemlist',
            name='page',
        ),
        migrations.RemoveField(
            model_name='itemtwocolumn',
            name='page',
        ),
    ]
