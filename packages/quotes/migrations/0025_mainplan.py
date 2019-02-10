# Generated by Django 2.1.3 on 2019-02-10 07:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0024_auto_20190202_0517'),
    ]

    operations = [
        migrations.CreateModel(
            name='MainPlan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vimm_enroll_id', models.CharField(db_index=True, max_length=20)),
                ('Plan_ID', models.CharField(db_index=True, max_length=600, verbose_name='Plan ID')),
                ('Name', models.CharField(choices=[('Freedom Spirit Plus', 'Freedom Spirit Plus'), ('Safeguard Critical Illness', 'Safeguard Critical Illness'), ('Foundation Dental', 'Foundation Dental'), ('USA Dental', 'USA Dental'), ('Everest STM', 'Everest STM'), ('LifeShield STM', 'LifeShield STM'), ('AdvantHealth STM', 'AdvantHealth STM'), ('Cardinal Choice', 'Cardinal Choice'), ('Health Choice', 'Health Choice'), ('Vitala Care', 'Vitala Care'), ('Legion Limited Medical', 'Legion Limited Medical')], db_index=True, max_length=100, verbose_name='Main Plan')),
                ('plan_name_for_img', models.CharField(max_length=600)),
                ('ins_type', models.CharField(choices=[('stm', 'STM'), ('lim', 'Limited'), ('ancillaries', 'ANCILLARIES')], max_length=200, verbose_name='Insurance Type')),
                ('plan_name', models.CharField(max_length=300, verbose_name='Plan name with details')),
                ('unique_url', models.CharField(blank=True, db_index=True, max_length=700, null=True)),
                ('quote_request_timestamp', models.IntegerField(blank=True, null=True)),
                ('Quote_ID', models.CharField(blank=True, max_length=600, null=True)),
                ('Access_Token', models.CharField(blank=True, max_length=700, null=True)),
                ('Premium', models.DecimalField(decimal_places=2, max_digits=20)),
                ('actual_premium', models.DecimalField(decimal_places=2, max_digits=20)),
                ('EnrollmentFee', models.DecimalField(decimal_places=2, max_digits=20)),
                ('Enrollment_Fee', models.DecimalField(decimal_places=2, max_digits=20)),
                ('TelaDocFee', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('TelaDoc_Fee', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('RxAdvocacy_Fee', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('RxAdvocacyFee', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('ChoiceValue_AdminFee', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('ChoiceValueSavings_Fee', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('Administrative_Fee', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('AdministrativeFee', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('VBP_Fee', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('Medsense_Fee', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('Association_Fee', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=20, null=True)),
                ('RealValueSavings_Fee', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('RealValueSavings_AdminFee', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('general_url', models.TextField()),
                ('general_plan_name', models.TextField()),
                ('Plan', models.CharField(blank=True, max_length=300, null=True, verbose_name='Main Plan sub category number')),
                ('Plan_Name', models.CharField(max_length=300)),
                ('month', models.CharField(blank=True, max_length=600, null=True)),
                ('option', models.TextField(blank=True, null=True)),
                ('Coinsurance_Percentage', models.TextField(blank=True, null=True)),
                ('out_of_pocket_value', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('coverage_max_value', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('Duration_Coverage', models.TextField(blank=True, null=True)),
                ('Deductible_Option', models.TextField(blank=True, null=True)),
                ('Payment_Option', models.TextField(blank=True, null=True)),
                ('Benefit_Amount', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('copay', models.TextField(blank=True, null=True)),
                ('copay_text', models.TextField(blank=True, null=True)),
                ('copay_2', models.TextField(blank=True, null=True)),
                ('copay_2_text', models.CharField(blank=True, max_length=1000, null=True)),
                ('stand_alone_addon_plan', models.BooleanField(default=False)),
                ('Note', models.TextField(blank=True, null=True)),
                ('stm_enroll', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='quotes.StmEnroll', verbose_name='Enroll')),
            ],
            options={
                'db_table': 'main_plan',
            },
        ),
    ]
