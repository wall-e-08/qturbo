from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from core import settings
from .us_states import states, states_list



class Leads(models.Model):
    zip_code = models.CharField(max_length=5)

    dob = models.DateField()

    gender = models.CharField(max_length=1)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}_{}".format(self.zip_code, self.gender)


class StmEnroll(models.Model):

    vimm_enroll_id = models.CharField(
        verbose_name=_("Customer ID"),
        max_length=20, unique=True
    )

    vimm_enroll_process_time = models.DateTimeField(
        auto_now_add=True
    )

    stm_name = models.TextField(
        verbose_name=_("Main Plan"),
        db_index=True
    )

    # response of successful enrollment
    ApplicantID = models.TextField(blank=True, null=True)

    Member_ID = models.TextField(blank=True, null=True)

    User_ID = models.TextField(blank=True, null=True)

    Password = models.CharField(max_length=200, blank=True, null=True)

    LoginURL = models.TextField(blank=True, null=True)

    Status = models.TextField(blank=True, null=True)

    Payment_Status_Date = models.DateField(blank=True, null=True)

    # applicant information
    First_Name = models.CharField(
        max_length=500,
        verbose_name=_("First Name")
    )

    Middle_Name = models.CharField(
        max_length=500,
        verbose_name=_("Middle Name"),
        blank=True, null=True
    )

    Last_Name = models.CharField(
        max_length=500,
        verbose_name=_("Last Name")
    )

    Gender = models.CharField(
        max_length=50,
        choices=(('Male', 'Male'), ('Female', 'Female'))
    )

    DOB = models.DateField(
        verbose_name=_("Date of Birth")
    )

    Occupation = models.CharField(
        max_length=50,
        verbose_name=_("Occupation"),
        blank=True, null=True
    )

    Age = models.IntegerField()

    Feet = models.IntegerField(blank=True, null=True)

    Inch = models.IntegerField(blank=True, null=True)

    Weight = models.IntegerField(blank=True, null=True)

    Address = models.TextField()

    City = models.TextField()

    State = models.CharField(
        max_length=2,
        choices=states
    )

    ZipCode = models.CharField(
        max_length=5,
        db_index=True
    )

    Email = models.EmailField(
        db_index=True
    )

    DayPhone = models.TextField()

    CellPhone = models.TextField()

    Mailing_Name = models.TextField()

    Mailing_Address = models.TextField()

    Mailing_City = models.TextField()

    Mailing_State = models.CharField(
        max_length=2,
        choices=states
    )

    Mailing_ZipCode = models.CharField(max_length=5)

    # TODO: Populate Question data in view
    question_data = models.TextField(
        blank=True, null=True
    )

    # enroll info
    Name_Enroll = models.TextField()

    Name_Auth = models.TextField()

    IP_Address = models.TextField()

    Effective_Date = models.DateField(
        verbose_name = _("Effective Date")
    )

    #TODO: Populate
    applicant_info = models.TextField(
        blank=True, null=True
    )

    esign_verification_starts = models.BooleanField(default=False)

    esign_verification_pending = models.BooleanField(default=False)

    esign_completed = models.BooleanField(default=False)

    last_esign_checked_at = models.DateTimeField(
        verbose_name=_("Last time when esign was checked"),
        blank=True,
        null=True,
    )

    esign_checked_and_enrolled_by_system = models.BooleanField(default=False)

    esign_verification_applicant_info = models.TextField(
        blank=True, null=True
    )

    app_url = models.CharField(
        max_length=250,
        unique=True,
        blank=True, null=True
    )
    # TODO: Now highest stage in model is 4. Need to make it 5
    stage = models.IntegerField(
        verbose_name=_("Application Stage"),
        default=0
    )

    enrolled = models.BooleanField(
        default=False,
        db_index=True
    )

    same_as_contact_address = models.BooleanField(
        default=False
    )

    Payment_Method = models.CharField(
        max_length=100,
        choices=(
            ("CreditCard", "Credit Card"),
            ("BankDraft", "Bank Draft")
        ),
        #TODO: Change It ASAP
        default='BankDraft', blank=True, null=True
    )


    # parents info
    Parent_First_Name = models.TextField(blank=True, null=True)

    Parent_Middle_Name = models.TextField(blank=True, null=True)

    Parent_Last_Name = models.TextField(blank=True, null=True)

    Parent_Gender = models.CharField(
        max_length=50,
        choices=(('Male', 'Male'), ('Female', 'Female')),
        blank=True, null=True
    )

    Parent_DOB = models.DateField(blank=True, null=True)

    Parent_Address = models.TextField(blank=True, null=True)

    Parent_City = models.TextField(blank=True, null=True)

    Parent_State = models.TextField(blank=True, null=True)

    Parent_ZipCode = models.TextField(blank=True, null=True)

    Parent_Email = models.EmailField(blank=True, null=True)

    Parent_DayPhone = models.TextField(blank=True, null=True)

    Parent_CellPhone = models.TextField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)

    processed_at = models.DateTimeField(
        verbose_name=_("Time When Processed by Verifier"),
        blank=True,
        null=True,
        db_index=True
    )

    processed = models.BooleanField(
        default=False
    )

    '''
        No need for saving bank info

    '''
    # payment - bank
    # Bank_Account_Name = models.CharField(
    #     max_length=75,
    #     blank=True, null=True
    # )
    #
    # Bank_Account_Class = models.CharField(
    #     max_length=50,
    #     choices=(
    #         ("Checking", "Checking"),
    #         ("Saving", "Saving")
    #     ),
    #     blank=True, null=True
    # )
    #
    # Bank_Account_Type = models.CharField(
    #     max_length=50,
    #     choices=(
    #         ("Personal", "Personal"),
    #         ("Business", "Business")
    #     ),
    #     blank=True, null=True
    # )
    #
    # Bank_Name = models.CharField(
    #     max_length=100,
    #     blank=True, null=True
    # )
    #
    # Bank_Routing_Number = models.CharField(
    #     max_length=30,
    #     blank=True, null=True
    # )
    #
    # Bank_Account_Number = models.CharField(
    #     max_length=30,
    #     blank=True, null=True
    # )
    #
    # Bank_Check_Number = models.CharField(
    #     max_length=30,
    #     blank=True, null=True
    # )


    Payment_Agree = models.BooleanField(
        default=False
    )

    enrolled_plan_res = models.TextField(
        blank=True, null=True
    )

    def get_absolute_url(self):
        return reverse('dashboard:enroll_detail',
                       args=[self.id,
                             self.vimm_enroll_id,
                             ])

    def applicant_name(self):
        return "{0} {1}".format(self.First_Name, self.Last_Name)

    def get_stm_plan(self):
        ancillaries_plans = settings.ANCILLARIES_PLANS
        # a1_plans = ['Apex Limited Medical', 'AdvancedHealth Limited Medical']
        # a1_ancillaries_plans = ["Discount Dental", "Amplified AD-D", "OneCare AME + CI", "Amplified CI", "TeleMedicine",
        #                         ]
        # agentra_plans = ['Smart Health Pass', "MEC", "Accidental Death & Dismemberment",
        #                  "Paul Revere Group Critical Care", "Colonial Life Group Critical Care",
        #                  "Paul Revere Group Accident", "Colonial Life Group Accident", "Bright Idea Dental"]

        if self.stm_name == 'Everest STM':
            return self.evereststm_set.get()
        if self.stm_name == 'LifeShield STM':
            return self.lifeshieldstm_set.get()
        if self.stm_name == 'Premier STM':
            return self.premierstm_set.get()
        if self.stm_name == 'Unified Health One':
            return self.unifiedlimited_set.get()
        if self.stm_name == 'Principle Advantage':
            return self.principlelimited_set.get()
        if self.stm_name == 'Rx Card':
            return self.rxcardplan_set.get()
        if self.stm_name == 'Cardinal Choice':
            return self.cardinalchoice_set.get()
        if self.stm_name == 'Vitala Care':
            return self.vitalacare_set.get()
        if self.stm_name == 'Health Choice':
            return self.healthchoice_set.get()
        if self.stm_name == 'Legion Limited Medical':
            return self.legionlimitedmedical_set.get()
        if self.stm_name == 'Protector 360':
            return self.protector360_set.get()
        if self.stm_name in ancillaries_plans:
            return self.standaloneaddonplan_set.get()
        # elif self.stm_name in a1_plans or self.stm_name in a1_ancillaries_plans:
        #     return self.mainplan_set.get()
        return None

    def get_applicant_parent_info(self):
        # if not self.applicant_is_child:
        #     return {}
        return {
            'Parent_First_Name': self.Parent_First_Name or '',
            'Parent_Middle_Name': self.Parent_Middle_Name or '',
            'Parent_Last_Name': self.Parent_Last_Name or '',
            'Parent_Gender': self.Parent_Gender or '',
            'Parent_DOB': self.Parent_DOB or '',
            'Parent_Address': self.Parent_Address or self.Address,
            'Parent_City': self.Parent_City or self.City,
            'Parent_State': self.Parent_State or self.State,
            'Parent_ZipCode': self.Parent_ZipCode or self.ZipCode,
            'Parent_Email': self.Parent_Email or '',
            'Parent_DayPhone': self.Parent_DayPhone or '',
            'Parent_CellPhone': self.Parent_CellPhone or '',

            'Name_Enroll': self.Name_Enroll or '',
            'Name_Auth': self.Name_Auth or '',
        }


    def get_billing_info(self):
        #TODO Make fields for billing address in model
        # if self.same_as_contact_address:
        return {
            'same_as_contact_address': True,
            'Billing_Address': self.Address,
            'Billing_City': self.City,
            'Billing_State': self.State,
            'Billing_ZipCode': self.ZipCode
        }
        # return {
        #     'same_as_contact_address': False,
        #     'Billing_Address': self.Billing_Address or self.Address,
        #     'Billing_City': self.Billing_City or self.City,
        #     'Billing_State': self.Billing_State or self.State,
        #     'Billing_ZipCode': self.Billing_ZipCode or self.ZipCode
        # }

    def get_payment_info(self):
        data = {
            # TODO: Implement Credit Card Transaction
            'Payment_Method': 'CreditCard',
            'Card_Type': None,
            'Card_Number': None,
            'Card_ExpirationMonth': None,
            'Card_ExpirationYear': None,
            'CardHolder_Name': None,
            'Bank_Account_Name': None,
            'Bank_Account_Class': None,
            'Bank_Account_Type': None,
            'Bank_Name': None,
            'Bank_Routing_Number': None,
            'Bank_Account_Number': None,
            'Bank_Check_Number': None,
            'Payment_Agree': self.Payment_Agree,
            # TODO: postdate
            # 'is_post_date': self.is_post_date,
        }
        if self.Payment_Method == 'CreditCard':
            data.update({
                'Card_Type': self.Card_Type,
                'Card_Number': self.Card_Number,
                'Card_ExpirationMonth': self.Card_ExpirationMonth,
                'Card_ExpirationYear': self.Card_ExpirationYear,
                'CC_CVV2': self.CC_CVV2 if self.CC_CVV2 else '',
                'CardHolder_Name': self.CardHolder_Name
            })
        if self.Payment_Method == 'BankDraft':
            data.update({
                'Bank_Account_Name': self.Bank_Account_Name,
                'Bank_Account_Class': self.Bank_Account_Class,
                'Bank_Account_Type': self.Bank_Account_Type,
                'Bank_Name': self.Bank_Name,
                'Bank_Routing_Number': self.Bank_Routing_Number,
                'Bank_Account_Number': self.Bank_Account_Number,
                'Bank_Check_Number': self.Bank_Check_Number
            })
        # TODO postdate
        # if self.is_post_date:
        #     data.update({
        #         'post_date': self.post_date
        #     })
        return data

    def get_billing_payment_info(self):
        data = self.get_billing_info()
        data.update(self.get_payment_info())
        return data




    def __str__(self):
        return "{0} {1}".format(self.First_Name, self.Last_Name)

    class Meta:
        verbose_name = _("Enroll")


class Dependent(models.Model):

    stm_enroll = models.ForeignKey(
        to=StmEnroll,
        verbose_name=_("Enroll"),
        on_delete=models.CASCADE
    )

    vimm_enroll_id = models.CharField(
        max_length=20
    )

    Relation = models.CharField(
        max_length=50,
        choices=(('Spouse', 'Spouse'), ('Child', 'Child'))
    )

    First_Name = models.TextField()

    Middle_Name = models.TextField(blank=True, null=True)

    Last_Name = models.TextField()

    Gender = models.CharField(
        max_length=50,
        choices=(('Male', 'Male'), ('Female', 'Female'))
    )

    DOB = models.DateField()

    Age = models.IntegerField(blank=True, null=True)

    Feet = models.IntegerField(blank=True, null=True)

    Inch = models.IntegerField(blank=True, null=True)

    Weight = models.IntegerField(blank=True, null=True)

    SSN = models.TextField(blank=True, null=True)

    def get_json_data(self):
        return {'vimm_enroll_id': self.vimm_enroll_id,
                'app_url': self.app_url,
                'Relation': self.Relation,
                'First_Name': self.First_Name,
                'Middle_Name': self.Middle_Name,
                'Last_Name': self.Last_Name,
                'Gender': self.Gender,
                'DOB': self.DOB,
                'Age': self.Age,
                'Feet': self.Feet,
                'Inch': self.Inch,
                'Weight': self.Weight,
                'SSN': self.SSN}


class StmPlanBase(models.Model):

    stm_enroll = models.ForeignKey(
        to=StmEnroll,
        verbose_name=_("Enroll"),
        on_delete=models.CASCADE
    )

    vimm_enroll_id = models.CharField(max_length=20)

    Plan_ID = models.TextField()

    Name = models.TextField()

    plan_name_for_img = models.TextField()

    month = models.TextField()

    plan_name = models.TextField()

    unique_url = models.TextField()

    Premium = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    actual_premium = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    option = models.TextField()

    Coinsurance_Percentage = models.TextField()

    out_of_pocket_value = models.TextField()

    coverage_max_value = models.TextField()

    Duration_Coverage = models.TextField()

    Deductible_Option = models.TextField()

    quote_request_timestamp = models.IntegerField()

    copay = models.TextField()

    copay_text = models.TextField()

    Quote_ID = models.TextField()

    Access_Token = models.TextField()

    def get_json_data(self):
        return {'vimm_enroll_id': self.vimm_enroll_id,
                'Name': self.Name,
                'plan_name': self.plan_name,
                'unique_url': self.unique_url,
                'Premium': str(self.Premium),
                'actual_premium': str(self.actual_premium),
                'option': self.option,
                'Coinsurance_Percentage': self.Coinsurance_Percentage,
                'out_of_pocket_value': self.out_of_pocket_value,
                'coverage_max_value': self.coverage_max_value,
                'Duration_Coverage': self.Duration_Coverage,
                'Deductible_Option': self.Deductible_Option,
                'quote_request_timestamp': self.quote_request_timestamp,
                'Quote_ID': self.Quote_ID,
                'Access_Token': self.Access_Token,
                'Plan_ID': self.Plan_ID}

    class Meta:
        abstract = True


class LifeshieldStm(StmPlanBase):

    Plan = models.TextField()

    Plan_Name = models.TextField(db_column='everest_plan_name')

    Coinsurance_Limit = models.TextField()

    ChoiceValueSavings_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2,
    )

    ChoiceValue_AdminFee = models.DecimalField(
        max_digits=20,
        decimal_places=2,
    )

    RealValueSavings_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    RealValueSavings_AdminFee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    VBP_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    EnrollmentFee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    TelaDoc_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    Medsense_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    RxAdvocacy_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    Enrollment_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    Payment_Option = models.TextField()

    Coverage_Max = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    Benefit_Amount = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    copay_2 = models.TextField()

    copay_2_text = models.TextField()

    def get_json_data(self):
        data = super().get_json_data()
        data.update({'Plan': self.Plan,
                     'ChoiceValueSavings_Fee': str(self.ChoiceValueSavings_Fee),
                     'ChoiceValue_AdminFee': str(self.ChoiceValue_AdminFee),
                     'RealValueSavings_Fee': str(self.RealValueSavings_Fee),
                     'RealValueSavings_AdminFee': str(self.RealValueSavings_AdminFee),
                     'VBP_Fee': str(self.VBP_Fee),
                     'EnrollmentFee': str(self.EnrollmentFee),
                     'TelaDoc_Fee': str(self.TelaDoc_Fee),
                     'Medsense_Fee': str(self.Medsense_Fee),
                     'RxAdvocacy_Fee': str(self.RxAdvocacy_Fee),
                     'Enrollment_Fee': str(self.Enrollment_Fee),
                     'Payment_Option': self.Payment_Option,
                     'Plan_Name': self.Plan_Name,
                     'Coverage_Max': str(self.Coverage_Max),
                     'Benefit_Amount': str(self.Benefit_Amount)})
        return data


class LimitedBase(models.Model):

    stm_enroll = models.ForeignKey(
        to=StmEnroll,
        verbose_name=_("Enroll"),
        on_delete=models.CASCADE
    )

    vimm_enroll_id = models.CharField(
        max_length=20,
        unique=True,
        db_index=True
    )

    Plan_ID = models.CharField(
        verbose_name=_("Plan ID"),
        max_length=600,
        db_index=True
    )

    Name = models.CharField(
        max_length=600,
        db_index=True
    )

    Lim_Plan_Name = models.CharField(
        max_length=200,
        db_index=True
    )

    plan_name_for_img = models.CharField(
        max_length=600,
        db_index=True
    )

    plan_name = models.CharField(
        max_length=600
    )

    unique_url = models.CharField(
        max_length=700,
        db_index=True
    )

    Premium = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    EnrollmentFee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    Enrollment_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    actual_premium = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    Quote_ID = models.CharField(
        max_length=600
    )

    Access_Token = models.CharField(
        max_length=700
    )

    quote_request_timestamp = models.IntegerField()

    def get_json_data(self):
        return {
            'vimm_enroll_id': self.vimm_enroll_id,
            'Plan_ID': self.Plan_ID,
            'Name': self.Name,
            'Lim_Plan_Name': self.Lim_Plan_Name,
            'plan_name_for_img': self.plan_name_for_img,
            'plan_name': self.plan_name,
            'unique_url': self.unique_url,
            'Premium': str(self.Premium),
            'EnrollmentFee': str(self.EnrollmentFee),
            'Enrollment_Fee': str(self.Enrollment_Fee),
            'actual_premium': str(self.actual_premium),
            'quote_request_timestamp': self.quote_request_timestamp,
            'Quote_ID': self.Quote_ID,
            'Access_Token': self.Access_Token,
        }

    class Meta:
        abstract = True


class CardinalChoice(LimitedBase):

    Plan_Type = models.CharField(
        max_length=500,
        choices=(
            ('Single Member', 'Single Member'),
            ('Member+1', 'Member+1'),
            ('Family', 'Family'),

        )
    )

    TelaDocFee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    TelaDoc_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    RxAdvocacy_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    RxAdvocacyFee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    ChoiceValue_AdminFee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    ChoiceValueSavings_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    RealValueSavings_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    RealValueSavings_AdminFee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    def get_json_data(self):
        data = super(CardinalChoice, self).get_json_data()
        data.update({
            'Plan_Type': self.Plan_Type,
            'TelaDocFee': str(self.TelaDocFee),
            'TelaDoc_Fee': str(self.TelaDoc_Fee),
            'RxAdvocacyFee': str(self.RxAdvocacyFee),
            'RxAdvocacy_Fee': str(self.RxAdvocacy_Fee),
            'ChoiceValue_AdminFee': str(self.ChoiceValue_AdminFee),
            'ChoiceValueSavings_Fee': str(self.ChoiceValueSavings_Fee),
            'RealValueSavings_Fee': str(self.RealValueSavings_Fee),
            'RealValueSavings_AdminFee': str(self.RealValueSavings_AdminFee),
        })
        return data

    class Meta:
        db_table = 'cardinal_choice'


class VitalaCare(LimitedBase):

    Plan_Type = models.CharField(
        max_length=500,
        choices=(
            ('Single Member', 'Single Member'),
            ('Member+1', 'Member+1'),
            ('Family', 'Family'),

        )
    )

    TelaDocFee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    TelaDoc_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    RxAdvocacy_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    RxAdvocacyFee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    ChoiceValue_AdminFee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    ChoiceValueSavings_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    # quote_request_timestamp = models.IntegerField(
    #     blank=True, null=True
    # ) # Not in nhaquotedb

    def get_json_data(self):
        data = super(VitalaCare, self).get_json_data()
        data.update({
            'Plan_Type': self.Plan_Type,
            'TelaDocFee': str(self.TelaDocFee),
            'TelaDoc_Fee': str(self.TelaDoc_Fee),
            'RxAdvocacyFee': str(self.RxAdvocacyFee),
            'RxAdvocacy_Fee': str(self.RxAdvocacy_Fee),
            'ChoiceValue_AdminFee': str(self.ChoiceValue_AdminFee),
            'ChoiceValueSavings_Fee': str(self.ChoiceValueSavings_Fee),
        })
        return data

    class Meta:
        db_table = 'vitala_care'


class AddonPlan(models.Model):

    stm_enroll = models.ForeignKey(
        to=StmEnroll,
        verbose_name=_("Enroll"),
        on_delete=models.CASCADE
    )

    vimm_enroll_id = models.CharField(max_length=20)

    stm_name = models.CharField(
        max_length=100,
        verbose_name=_("Main Plan"),
        choices=(
            ('Everest STM', 'Everest STM'),
            ('LifeShield STM', 'LifeShield STM'),
            ('HealtheFlex STM', 'HealtheFlex STM'),
            ('HealtheMed STM', 'HealtheMed STM'),
            ('Premier STM', 'Premier STM'),
            ('Sage STM', 'Sage STM'),
            ('Principle Advantage', 'Principle Advantage'),
        )
    )

    addon_id = models.IntegerField()

    Name = models.TextField()

    carrier_name = models.TextField(blank=True, null=True)

    carrier_id = models.TextField(blank=True, null=True)

    Premium = models.DecimalField(
        verbose_name=_("Premium"),
        max_digits=20,
        decimal_places=2
    )

    actual_premium = models.DecimalField(
        verbose_name=_("Actual Premium"),
        max_digits=20,
        decimal_places=2
    )

    AdministrativeFee = models.DecimalField(
        verbose_name=_("Administrative Fee"),
        max_digits=20,
        decimal_places=2
    )

    EnrollmentFee = models.DecimalField(
        verbose_name=_("Enrollment Fee"),
        max_digits=20,
        decimal_places=2
    )

    MedsenseFee = models.DecimalField(
        verbose_name=_("Medsense Fee"),
        max_digits=20,
        decimal_places=2
    )

    Embeded = models.CharField(max_length=100)

    Plan = models.CharField(max_length=100, blank=True, null=True)

    Plan_Code = models.CharField(max_length=100, blank=True, null=True)

    Deductible = models.CharField(max_length=100, blank=True, null=True)

    Member_ID = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return "(smt_name: {0}, addon_id: {1}, name: {2}, 'premium': {3})".format(self.stm_name, self.addon_id,
                                                                                  self.Name, self.Premium)

    def data_as_dict(self):
        data = dict(
            stm_name=self.stm_name,
            addon_id=self.addon_id,
            Name=self.Name,
            carrier_name=self.carrier_name,
            carrier_id=self.carrier_id,
            Premium=str(self.Premium),
            AdministrativeFee=str(self.AdministrativeFee),
            EnrollmentFee=str(self.EnrollmentFee),
            MedsenseFee=str(self.MedsenseFee),
            Embeded=self.Embeded,
            actual_premium=str(self.actual_premium),
        )
        if int(self.addon_id) == 38:
            data.update({
                'Plan': self.Plan,
                'Plan_Code': self.Plan_Code,
                'Deductible': self.Deductible,
            })
        return data

    def get_json_data(self):
        return self.data_as_dict()
