# Generated by Django 2.1.3 on 2019-01-20 07:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0010_auto_20190120_0637'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generaltopic',
            name='faq_heading',
            field=models.TextField(max_length=300),
        ),
        migrations.AlterField(
            model_name='generaltopic',
            name='quote_heading',
            field=models.TextField(max_length=300, verbose_name='All page quote Heading'),
        ),
        migrations.AlterField(
            model_name='generaltopic',
            name='review_heading',
            field=models.TextField(max_length=500),
        ),
        migrations.AlterField(
            model_name='generaltopic',
            name='service_heading',
            field=models.TextField(max_length=300, verbose_name='Service Heading'),
        ),
        migrations.AlterField(
            model_name='generaltopic',
            name='service_items',
            field=models.TextField(max_length=1000),
        ),
        migrations.AlterField(
            model_name='generaltopic',
            name='service_sub_heading',
            field=models.TextField(max_length=300, verbose_name='Service Sub Heading'),
        ),
        migrations.AlterField(
            model_name='generaltopic',
            name='top_quote_heading',
            field=models.TextField(max_length=500),
        ),
        migrations.AlterField(
            model_name='generaltopic',
            name='top_quote_sub_heading',
            field=models.TextField(max_length=500),
        ),
    ]
