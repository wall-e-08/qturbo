# Generated by Django 2.1.3 on 2019-01-17 08:54

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0007_auto_20190116_1213'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generaltopic',
            name='faqs',
            field=django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=500), size=2), size=None),
        ),
    ]
