# Generated by Django 2.1.3 on 2018-12-23 12:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0013_auto_20181223_1053'),
    ]

    operations = [
        migrations.AddField(
            model_name='dependent',
            name='Tobacco',
            field=models.TextField(blank=True, null=True),
        ),
    ]