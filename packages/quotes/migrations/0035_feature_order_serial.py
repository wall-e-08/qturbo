# Generated by Django 2.1.3 on 2019-03-05 06:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0034_auto_20190305_0557'),
    ]

    operations = [
        migrations.AddField(
            model_name='feature',
            name='order_serial',
            field=models.IntegerField(default=0),
        ),
    ]