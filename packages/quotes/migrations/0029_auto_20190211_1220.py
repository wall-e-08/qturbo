# Generated by Django 2.1.3 on 2019-02-11 12:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0028_auto_20190211_1214'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='advanthealthstm',
            name='stm_enroll',
        ),
        migrations.DeleteModel(
            name='AdvanthealthStm',
        ),
    ]
