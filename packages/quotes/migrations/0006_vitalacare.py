# Generated by Django 2.1.3 on 2018-12-18 08:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0005_addonplan'),
    ]

    operations = [
        migrations.CreateModel(
            name='VitalaCare',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vimm_enroll_id', models.CharField(db_index=True, max_length=20, unique=True)),
                ('Plan_ID', models.CharField(db_index=True, max_length=600, verbose_name='Plan ID')),
                ('Name', models.CharField(db_index=True, max_length=600)),
                ('Lim_Plan_Name', models.CharField(db_index=True, max_length=200)),
                ('plan_name_for_img', models.CharField(db_index=True, max_length=600)),
                ('plan_name', models.CharField(max_length=600)),
                ('unique_url', models.CharField(db_index=True, max_length=700)),
                ('Premium', models.DecimalField(decimal_places=2, max_digits=20)),
                ('EnrollmentFee', models.DecimalField(decimal_places=2, max_digits=20)),
                ('Enrollment_Fee', models.DecimalField(decimal_places=2, max_digits=20)),
                ('actual_premium', models.DecimalField(decimal_places=2, max_digits=20)),
                ('Quote_ID', models.CharField(max_length=600)),
                ('Access_Token', models.CharField(max_length=700)),
                ('quote_request_timestamp', models.IntegerField()),
                ('Plan_Type', models.CharField(choices=[('Single Member', 'Single Member'), ('Member+1', 'Member+1'), ('Family', 'Family')], max_length=500)),
                ('TelaDocFee', models.DecimalField(decimal_places=2, max_digits=20)),
                ('TelaDoc_Fee', models.DecimalField(decimal_places=2, max_digits=20)),
                ('RxAdvocacy_Fee', models.DecimalField(decimal_places=2, max_digits=20)),
                ('RxAdvocacyFee', models.DecimalField(decimal_places=2, max_digits=20)),
                ('ChoiceValue_AdminFee', models.DecimalField(decimal_places=2, max_digits=20)),
                ('ChoiceValueSavings_Fee', models.DecimalField(decimal_places=2, max_digits=20)),
                ('stm_enroll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='quotes.StmEnroll', verbose_name='Enroll')),
            ],
            options={
                'db_table': 'vitala_care',
            },
        ),
    ]
