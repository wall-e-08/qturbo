# Generated by Django 2.1.3 on 2019-01-06 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0016_auto_20190103_1246'),
    ]

    operations = [
        migrations.AddField(
            model_name='advanthealthstm',
            name='Association_Fee',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=20, null=True),
        ),
    ]
