# Generated by Django 2.1.3 on 2019-01-29 05:45

from django.db import migrations, models
import quotes.utils


class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0020_auto_20190123_1056'),
    ]

    operations = [
        migrations.AddField(
            model_name='benefitsandcoverage',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=quotes.utils.get_img_path, verbose_name='Image File'),
        ),
    ]
