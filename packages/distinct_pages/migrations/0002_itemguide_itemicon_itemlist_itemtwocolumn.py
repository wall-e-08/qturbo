# Generated by Django 2.1.3 on 2018-12-20 10:56

import distinct_pages.utils
from django.db import migrations, models
import django.db.models.deletion
import djrichtextfield.models


class Migration(migrations.Migration):

    dependencies = [
        ('distinct_pages', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ItemGuide',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField()),
                ('url_text', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='ItemIcon',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('svg_icon', models.TextField(blank=True, null=True, verbose_name='SVG Code')),
                ('img_icon', models.ImageField(blank=True, null=True, upload_to=distinct_pages.utils.get_img_path, verbose_name='Image File')),
            ],
        ),
        migrations.CreateModel(
            name='ItemList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', djrichtextfield.models.RichTextField()),
                ('url', models.URLField(blank=True, null=True)),
                ('icon', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='distinct_pages.ItemIcon')),
            ],
        ),
        migrations.CreateModel(
            name='ItemTwoColumn',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=200, null=True)),
                ('img', models.ImageField(blank=True, null=True, upload_to=distinct_pages.utils.get_img_path, verbose_name='Single Image')),
                ('content', djrichtextfield.models.RichTextField()),
                ('url', models.URLField(blank=True, null=True)),
                ('url_text', models.CharField(blank=True, max_length=200, null=True)),
            ],
        ),
    ]
