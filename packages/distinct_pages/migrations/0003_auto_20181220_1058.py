# Generated by Django 2.1.3 on 2018-12-20 10:58

from django.db import migrations
import djrichtextfield.models


class Migration(migrations.Migration):

    dependencies = [
        ('distinct_pages', '0002_itemguide_itemicon_itemlist_itemtwocolumn'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemlist',
            name='content',
            field=djrichtextfield.models.RichTextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='page',
            name='content',
            field=djrichtextfield.models.RichTextField(blank=True, null=True),
        ),
    ]
