from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from multiselectfield import MultiSelectField
from djrichtextfield.models import RichTextField
from core import settings
from .us_states import states, states_list
from .utils import get_img_path, get_img_path_by_filename


class PatchedMultiSelectField(MultiSelectField):
  def value_to_string(self, obj):
    value = self.value_from_object(obj)
    return self.get_prep_value(value)


class Carrier(models.Model):
    plan_id = models.CharField(
        blank=True, null=True,
        max_length=100
    )

    ins_type = models.CharField(
        max_length=100,
        choices=(
            ('stm', 'STM'),
            ('lim', 'Limited'),
            ('anc', 'ANC'),
        ),
        verbose_name=_("Insurance Type"),
        db_index=True
    )

    name = models.CharField(
        max_length=100,
        choices=settings.MAIN_PLANS,
        verbose_name=_("Name"),
        unique=True,
        db_index=True
    )

    allowed_state = PatchedMultiSelectField(
        verbose_name=_("States"),
        max_length=500,
        choices=states,
        default=states_list,
        blank=True, null=True
    )

    has_question_api = models.BooleanField(
        default=False
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    child_allowed = models.BooleanField(
        default=True    )

    spouse_allowed = models.BooleanField(
        default=True
    )

    def __str__(self):
        return self.name


    # @property
    # def plan_id(self):
    #     """Is this necessary?
    #     :return: int
    #     """
    #     return self.plan_id

    @classmethod
    def get_carrier_ins_type(cls, carrier_name):
        try:
            obj = cls.objects.get(name=carrier_name)
        except cls.DoesNotExist:
            return None
        return obj.ins_type

    @classmethod
    def get_provider_choices(cls):
        choices = []
        for obj in cls.objects.filter(is_active=True):
            choices.append([obj.name, obj.name])
        return choices

    def get_carrier_available_states(self):
        """
        :return: All the available states set n admin/db
        """
        return self.allowed_state

    def get_carrier_active_state(self):
        """
        :return: True if is_active is set true in model
        """
        return self.is_active

    def get_sub_plan_list(self):
        available_sub_plan = self.carriersubplan_set.filter(carrier=self).order_by('sub_plan_name')
        available_sub_plan_name = list(set([sub_plan.sub_plan_name for sub_plan in available_sub_plan]))
        available_sub_plan_name.sort()
        return available_sub_plan_name

    def get_sub_plan_first(self):
        return self.get_sub_plan_list()[0] if self.get_sub_plan_list() else None


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
        verbose_name=_("First Name"),
        blank=True, null=True
    )

    Middle_Name = models.CharField(
        max_length=500,
        verbose_name=_("Middle Name"),
        blank=True, null=True
    )

    Last_Name = models.CharField(
        max_length=500,
        verbose_name=_("Last Name"),
        blank=True, null=True
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

    Address = models.TextField(blank=True, null=True)

    City = models.TextField(blank=True, null=True)

    State = models.CharField(
        max_length=2,
        choices=states
    )

    ZipCode = models.CharField(
        max_length=5,
        db_index=True
    )

    Email = models.EmailField(
        db_index=True,
        blank=True, null=True
    )

    DayPhone = models.TextField(blank=True, null=True)

    CellPhone = models.TextField(blank=True, null=True)

    Mailing_Name = models.TextField(blank=True, null=True)

    Mailing_Address = models.TextField(blank=True, null=True)

    Mailing_City = models.TextField(blank=True, null=True)

    Mailing_State = models.CharField(
        max_length=2,
        choices=states,
        blank=True, null=True
    )

    Mailing_ZipCode = models.CharField(max_length=5, blank=True, null=True)

    Applicant_is_Child = models.BooleanField(default=False)

    Tobacco = models.CharField(null=True, blank=True, max_length=1)

    # TODO: Populate Question data in view
    question_data = models.TextField(
        blank=True, null=True
    )

    # enroll info
    Name_Enroll = models.TextField()

    Name_Auth = models.TextField(blank=True, null=True)

    IP_Address = models.TextField(blank=True, null=True)

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
        return self.mainplan_set.get()

    def get_applicant_parent_info(self):
        if not self.Applicant_is_Child:
            return {}
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
        # TODO Make fields for billing address in model
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

    def get_applicant_info_for_update(self):
        stm_plan_obj = self.get_stm_plan()
        plan = stm_plan_obj.get_json_data()
        data = {
            'Plan_ID': plan['Plan_ID'],
            'Name': plan['Name'],
            'Quote_ID': plan['Quote_ID'],
            'Access_Token': plan["Access_Token"],
            'First_Name': self.First_Name,
            'Middle_Name': self.Middle_Name,
            'Last_Name': self.Last_Name,
            'Address': self.Address,
            'City': self.City,
            'Email': self.Email,
            'DayPhone': self.DayPhone,
            'Mailing_Name': self.Mailing_Name,
            'Mailing_Address': self.Mailing_Address,
            'Mailing_City': self.Mailing_City,
            'Mailing_State': self.Mailing_State,
            'Mailing_ZipCode': self.Mailing_ZipCode,

            'Payment_Method': self.Payment_Method,
            'same_as_contact_address': self.same_as_contact_address,
            'Billing_Address': self.Address,
            'Billing_City': self.City,
            'Billing_State': self.State,
            'Billing_ZipCode': self.ZipCode,

            'Name_Enroll': self.Name_Enroll,
            'Name_Auth': self.Name_Auth,
        }
        if self.Applicant_is_Child:
            data.update({
                'Parent_First_Name': self.Parent_First_Name or '',
                'Parent_Middle_Name': self.Parent_Middle_Name or '',
                'Parent_Last_Name': self.Parent_Last_Name or '',
                'Parent_Gender': self.Parent_Gender or '',
                'Parent_DOB': self.Parent_DOB.strftime('%Y-%m-%d') or '',
                'Parent_Address': self.Parent_Address or self.Address,
                'Parent_City': self.Parent_City or self.City,
                'Parent_State': self.Parent_State or self.State,
                'Parent_ZipCode': self.Parent_ZipCode or self.ZipCode,
                'Parent_Email': self.Parent_Email or '',
                'Parent_DayPhone': self.Parent_DayPhone or '',
                'Parent_CellPhone': self.Parent_CellPhone or '',
            })
        return data


    def __str__(self):
        return "{0} {1}".format(self.First_Name, self.Last_Name)

    class Meta:
        verbose_name = _("Enroll")


class Leads(models.Model):

    stm_enroll = models.ForeignKey(
        to=StmEnroll,
        verbose_name=_("Enroll"),
        on_delete=models.SET_NULL,

        null=True, blank=True
    )

    vimm_enroll_id = models.CharField(
        max_length=20,
        null=True, blank=True
    )

    Zip_Code = models.CharField(max_length=5)

    DOB = models.DateField()

    Gender = models.CharField(max_length=6)

    created = models.DateTimeField(auto_now_add=True)

    quote_store_key = models.CharField(max_length=500)

    def __str__(self):
        return "{}_{}".format(self.zip_code, self.gender)


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

    First_Name = models.TextField(blank=True, null=True)

    Middle_Name = models.TextField(blank=True, null=True)

    Last_Name = models.TextField(blank=True, null=True)

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

    Tobacco = models.TextField(blank=True, null=True, max_length=1)


    def get_json_data(self):
        return {'vimm_enroll_id': self.vimm_enroll_id,
                'app_url': self.stm_enroll.app_url,
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


# class StmPlanBase(models.Model):
#
#     stm_enroll = models.ForeignKey(
#         to=StmEnroll,
#         verbose_name=_("Enroll"),
#         on_delete=models.CASCADE
#     )
#
#     vimm_enroll_id = models.CharField(max_length=20)
#
#     Plan_ID = models.TextField()
#
#     Name = models.TextField()
#
#     plan_name_for_img = models.TextField()
#
#     month = models.TextField()
#
#     plan_name = models.TextField()
#
#     unique_url = models.TextField()
#
#     general_url = models.TextField()
#
#     general_plan_name = models.TextField()
#
#     Premium = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     actual_premium = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     option = models.TextField()
#
#     Coinsurance_Percentage = models.TextField()
#
#     out_of_pocket_value = models.TextField()
#
#     coverage_max_value = models.TextField()
#
#     Duration_Coverage = models.TextField()
#
#     Deductible_Option = models.TextField()
#
#     quote_request_timestamp = models.IntegerField()
#
#     copay = models.TextField()
#
#     copay_text = models.TextField()
#
#     Quote_ID = models.TextField()
#
#     Access_Token = models.TextField()
#
#     def get_json_data(self):
#         return {'vimm_enroll_id': self.vimm_enroll_id,
#                 'Name': self.Name,
#                 'plan_name': self.plan_name,
#                 'general_plan_name': self.general_plan_name,
#                 'unique_url': self.unique_url,
#                 'general_url': self.general_url,
#                 'Premium': str(self.Premium),
#                 'actual_premium': str(self.actual_premium),
#                 'option': self.option,
#                 'Coinsurance_Percentage': self.Coinsurance_Percentage,
#                 'out_of_pocket_value': self.out_of_pocket_value,
#                 'coverage_max_value': self.coverage_max_value,
#                 'Duration_Coverage': self.Duration_Coverage,
#                 'Deductible_Option': self.Deductible_Option,
#                 'quote_request_timestamp': self.quote_request_timestamp,
#                 'Quote_ID': self.Quote_ID,
#                 'Access_Token': self.Access_Token,
#                 'Plan_ID': self.Plan_ID}
#
#     class Meta:
#         abstract = True


# class LifeshieldStm(StmPlanBase):
#
#     Plan = models.TextField()
#
#     Plan_Name = models.TextField(db_column='everest_plan_name')
#
#     Coinsurance_Limit = models.TextField()
#
#     ChoiceValueSavings_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2,
#     )
#
#     ChoiceValue_AdminFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2,
#     )
#
#     RealValueSavings_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     RealValueSavings_AdminFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     VBP_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     EnrollmentFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     TelaDoc_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     Medsense_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     RxAdvocacy_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     Enrollment_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     Payment_Option = models.TextField()
#
#     Coverage_Max = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     Benefit_Amount = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     copay_2 = models.TextField()
#
#     copay_2_text = models.TextField()
#
#     def get_json_data(self):
#         data = super().get_json_data()
#         data.update({'Plan': self.Plan,
#                      'ChoiceValueSavings_Fee': str(self.ChoiceValueSavings_Fee),
#                      'ChoiceValue_AdminFee': str(self.ChoiceValue_AdminFee),
#                      'RealValueSavings_Fee': str(self.RealValueSavings_Fee),
#                      'RealValueSavings_AdminFee': str(self.RealValueSavings_AdminFee),
#                      'VBP_Fee': str(self.VBP_Fee),
#                      'EnrollmentFee': str(self.EnrollmentFee),
#                      'TelaDoc_Fee': str(self.TelaDoc_Fee),
#                      'Medsense_Fee': str(self.Medsense_Fee),
#                      'RxAdvocacy_Fee': str(self.RxAdvocacy_Fee),
#                      'Enrollment_Fee': str(self.Enrollment_Fee),
#                      'Payment_Option': self.Payment_Option,
#                      'Plan_Name': self.Plan_Name,
#                      'Coverage_Max': str(self.Coverage_Max),
#                      'Benefit_Amount': str(self.Benefit_Amount)})
#         return data


# class AdvanthealthStm(StmPlanBase):
#
#     Plan = models.TextField()
#
#     Plan_Name = models.TextField(db_column='everest_plan_name')
#
#     Coinsurance_Limit = models.TextField()
#
#     ChoiceValueSavings_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2,
#     )
#
#     ChoiceValue_AdminFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2,
#     )
#
#     RealValueSavings_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     RealValueSavings_AdminFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     VBP_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     EnrollmentFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     TelaDoc_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     Medsense_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     RxAdvocacy_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     Association_Fee = models.DecimalField(
#         default=0,
#         max_digits=20,
#         decimal_places=2,
#         blank=True, null=True
#
#     )
#
#     Enrollment_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     Payment_Option = models.TextField()
#
#     Coverage_Max = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     Benefit_Amount = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     copay_2 = models.TextField()
#
#     copay_2_text = models.TextField()
#
#     def get_json_data(self):
#         data = super().get_json_data()
#         data.update({'Plan': self.Plan,
#                      'ChoiceValueSavings_Fee': str(self.ChoiceValueSavings_Fee),
#                      'ChoiceValue_AdminFee': str(self.ChoiceValue_AdminFee),
#                      'RealValueSavings_Fee': str(self.RealValueSavings_Fee),
#                      'RealValueSavings_AdminFee': str(self.RealValueSavings_AdminFee),
#                      'VBP_Fee': str(self.VBP_Fee),
#                      'EnrollmentFee': str(self.EnrollmentFee),
#                      'TelaDoc_Fee': str(self.TelaDoc_Fee),
#                      'Medsense_Fee': str(self.Medsense_Fee),
#                      'RxAdvocacy_Fee': str(self.RxAdvocacy_Fee),
#                      'Enrollment_Fee': str(self.Enrollment_Fee),
#                      'Payment_Option': self.Payment_Option,
#                      'Plan_Name': self.Plan_Name,
#                      'Coverage_Max': str(self.Coverage_Max),
#                      'Benefit_Amount': str(self.Benefit_Amount)})
#         return data


# class LimitedBase(models.Model):
#
#     stm_enroll = models.ForeignKey(
#         to=StmEnroll,
#         verbose_name=_("Enroll"),
#         on_delete=models.CASCADE
#     )
#
#     vimm_enroll_id = models.CharField(
#         max_length=20,
#         unique=True,
#         db_index=True
#     )
#
#     Plan_ID = models.CharField(
#         verbose_name=_("Plan ID"),
#         max_length=600,
#         db_index=True
#     )
#
#     Name = models.CharField(
#         max_length=600,
#         db_index=True
#     )
#
#     Lim_Plan_Name = models.CharField(
#         max_length=200,
#         db_index=True
#     )
#
#     plan_name_for_img = models.CharField(
#         max_length=600,
#         db_index=True
#     )
#
#     plan_name = models.CharField(
#         max_length=600
#     )
#
#     unique_url = models.CharField(
#         max_length=700,
#         db_index=True
#     )
#
#     Premium = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     EnrollmentFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     Enrollment_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     actual_premium = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     Quote_ID = models.CharField(
#         max_length=600
#     )
#
#     Access_Token = models.CharField(
#         max_length=700
#     )
#
#     quote_request_timestamp = models.IntegerField()
#
#     def get_json_data(self):
#         return {
#             'vimm_enroll_id': self.vimm_enroll_id,
#             'Plan_ID': self.Plan_ID,
#             'Name': self.Name,
#             'Lim_Plan_Name': self.Lim_Plan_Name,
#             'plan_name_for_img': self.plan_name_for_img,
#             'plan_name': self.plan_name,
#             'unique_url': self.unique_url,
#             'Premium': str(self.Premium),
#             'EnrollmentFee': str(self.EnrollmentFee),
#             'Enrollment_Fee': str(self.Enrollment_Fee),
#             'actual_premium': str(self.actual_premium),
#             'quote_request_timestamp': self.quote_request_timestamp,
#             'Quote_ID': self.Quote_ID,
#             'Access_Token': self.Access_Token,
#         }
#
#     class Meta:
#         abstract = True


# class CardinalChoice(LimitedBase):
#
#     Plan_Type = models.CharField(
#         max_length=500,
#         choices=(
#             ('Single Member', 'Single Member'),
#             ('Member+1', 'Member+1'),
#             ('Family', 'Family'),
#
#         )
#     )
#
#     TelaDocFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     TelaDoc_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     RxAdvocacy_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     RxAdvocacyFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     ChoiceValue_AdminFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     ChoiceValueSavings_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     RealValueSavings_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     RealValueSavings_AdminFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     def get_json_data(self):
#         data = super(CardinalChoice, self).get_json_data()
#         data.update({
#             'Plan_Type': self.Plan_Type,
#             'TelaDocFee': str(self.TelaDocFee),
#             'TelaDoc_Fee': str(self.TelaDoc_Fee),
#             'RxAdvocacyFee': str(self.RxAdvocacyFee),
#             'RxAdvocacy_Fee': str(self.RxAdvocacy_Fee),
#             'ChoiceValue_AdminFee': str(self.ChoiceValue_AdminFee),
#             'ChoiceValueSavings_Fee': str(self.ChoiceValueSavings_Fee),
#             'RealValueSavings_Fee': str(self.RealValueSavings_Fee),
#             'RealValueSavings_AdminFee': str(self.RealValueSavings_AdminFee),
#         })
#         return data
#
#     class Meta:
#         db_table = 'cardinal_choice'


# class VitalaCare(LimitedBase):
#
#     Plan_Type = models.CharField(
#         max_length=500,
#         choices=(
#             ('Single Member', 'Single Member'),
#             ('Member+1', 'Member+1'),
#             ('Family', 'Family'),
#
#         )
#     )
#
#     TelaDocFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     TelaDoc_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     RxAdvocacy_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     RxAdvocacyFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     ChoiceValue_AdminFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     ChoiceValueSavings_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     # quote_request_timestamp = models.IntegerField(
#     #     blank=True, null=True
#     # ) # Not in nhaquotedb
#
#     def get_json_data(self):
#         data = super(VitalaCare, self).get_json_data()
#         data.update({
#             'Plan_Type': self.Plan_Type,
#             'TelaDocFee': str(self.TelaDocFee),
#             'TelaDoc_Fee': str(self.TelaDoc_Fee),
#             'RxAdvocacyFee': str(self.RxAdvocacyFee),
#             'RxAdvocacy_Fee': str(self.RxAdvocacy_Fee),
#             'ChoiceValue_AdminFee': str(self.ChoiceValue_AdminFee),
#             'ChoiceValueSavings_Fee': str(self.ChoiceValueSavings_Fee),
#         })
#         return data
#
#     class Meta:
#         db_table = 'vitala_care'


# class HealthChoice(LimitedBase):
#
#     Plan_Type = models.CharField(
#         max_length=500,
#         choices=(
#             ('Single Member', 'Single Member'),
#             ('Member+1', 'Member+1'),
#             ('Family', 'Family'),
#
#         )
#     )
#
#     TelaDocFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     TelaDoc_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     RxAdvocacy_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     RxAdvocacyFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     ChoiceValue_AdminFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     ChoiceValueSavings_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     def get_json_data(self):
#         data = super(HealthChoice, self).get_json_data()
#         data.update({
#             'Plan_Type': self.Plan_Type,
#             'TelaDocFee': str(self.TelaDocFee),
#             'TelaDoc_Fee': str(self.TelaDoc_Fee),
#             'RxAdvocacyFee': str(self.RxAdvocacyFee),
#             'RxAdvocacy_Fee': str(self.RxAdvocacy_Fee),
#             'ChoiceValue_AdminFee': str(self.ChoiceValue_AdminFee),
#             'ChoiceValueSavings_Fee': str(self.ChoiceValueSavings_Fee),
#         })
#         return data
#
#     class Meta:
#         db_table = 'health_choice'


# class LegionLimitedMedical(LimitedBase):
#
#     Plan_Type = models.CharField(
#         max_length=500,
#         choices=(
#             ('Single Member', 'Single Member'),
#             ('Member+1', 'Member+1'),
#             ('Family', 'Family'),
#
#         )
#     )
#
#     TelaDocFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     TelaDoc_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     RxAdvocacy_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     RxAdvocacyFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     ChoiceValue_AdminFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2,
#     )
#
#     ChoiceValueSavings_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2,
#     )
#
#     def get_json_data(self):
#         data = super(LegionLimitedMedical, self).get_json_data()
#         data.update({
#             'Plan_Type': self.Plan_Type,
#             'TelaDocFee': str(self.TelaDocFee),
#             'TelaDoc_Fee': str(self.TelaDoc_Fee),
#             'RxAdvocacyFee': str(self.RxAdvocacyFee),
#             'RxAdvocacy_Fee': str(self.RxAdvocacy_Fee),
#             'ChoiceValue_AdminFee': str(self.ChoiceValue_AdminFee),
#             'ChoiceValueSavings_Fee': str(self.ChoiceValueSavings_Fee),
#         })
#         return data
#
#     class Meta:
#         db_table = 'legion_limited_medical'


# --- Unified Model for all main plans ---

class MainPlan(models.Model):
    """
    Merged plan model for all main plan. Some of the fields have been added here cutting from previous StmEnroll model.
    Besides, all the individual plan models are merged here for hii and a1 plans.

    Changed Field:
        --------------------
        previous -> current
        --------------------

        For previous Hii (lim) model:
            Lim_Plan_Name -> Plan_Name

        For previous Ancillaries plan model (StandAlonePlan):
            Lim_Plan_Name -> Plan_Name
    """

    stm_enroll = models.ForeignKey(
        StmEnroll,
        on_delete=models.CASCADE,
        verbose_name=_("Enroll"),
        unique=True,
    )

    vimm_enroll_id = models.CharField(
        max_length=20,
        db_index=True
    )

    Plan_ID = models.CharField(
        verbose_name=_("Plan ID"),
        max_length=600,
        db_index=True
    )

    Name = models.CharField(
        verbose_name=_("Main Plan"),
        max_length=100,
        choices=settings.MAIN_PLANS,
        db_index=True
    )

    plan_name_for_img = models.CharField(
        max_length=600
    )

    ins_type = models.CharField(
        max_length=200,
        choices=(
            ('stm', 'STM'),
            ('lim', 'Limited'),
            ('ancillaries', 'ANCILLARIES'),
        ),
        verbose_name=_("Insurance Type"),
    )

    plan_name = models.CharField(
        verbose_name=_("Plan name with details"),
        max_length=300,
    ) # TODO: plan_name_long


    unique_url = models.CharField(
        max_length=700,
        db_index=True,
        blank=True, null=True
    )

    quote_request_timestamp = models.IntegerField(
        blank=True, null=True
    )

    Quote_ID = models.CharField(
        max_length=600,
        blank=True, null=True
    )

    paid = models.BooleanField(
        default=False
    )

    Access_Token = models.CharField(
        max_length=700,
        blank=True, null=True
    )

    Premium = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    actual_premium = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    # Effective_Date = models.ForeignKey(
    #     to=StmEnroll.Effective_Date,
    #     verbose_name=_("Effective Date"),
    #     null=True, blank=True,
    #     db_index=True
    # )

    EnrollmentFee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    Enrollment_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )


    TelaDocFee = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True, null=True
    )

    TelaDoc_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True, null=True
    )

    RxAdvocacy_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True, null=True
    )

    RxAdvocacyFee = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True, null=True
    )

    ChoiceValue_AdminFee = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True, null=True
    )

    ChoiceValueSavings_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True, null=True
    )

    Administrative_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True, null=True
    )

    AdministrativeFee = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True, null=True
    )

    VBP_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True, null=True
    )

    Medsense_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True, null=True
    )

    Association_Fee = models.DecimalField(
        default=0,
        max_digits=20,
        decimal_places=2,
        blank=True, null=True

    )

    RealValueSavings_Fee = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True, null=True
    )

    RealValueSavings_AdminFee = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True, null=True
    )
    
    #   --------
    #   stm plan
    #   --------
    
    general_url = models.TextField()

    general_plan_name = models.TextField()

    Plan = models.CharField(
        verbose_name=_("Main Plan sub category number"),
        max_length=300,
        blank=True, null=True
    ) # TODO: plan_number

    Plan_Name = models.CharField(
        max_length=300,
    ) # TODO: sub_plan_name


    month = models.CharField(
        max_length=600,
        blank=True, null=True
    )

    option = models.TextField(
        blank=True, null=True
    )


    Coinsurance_Percentage = models.TextField(blank=True, null=True)


    Benefit_Amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True, null=True
    )

    out_of_pocket_value = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True, null=True
    )

    coverage_max_value = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True, null=True
    )

    Coverage_Max = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True, null=True
    )

    Duration_Coverage = models.TextField(blank=True, null=True)

    Deductible_Option = models.TextField(blank=True, null=True)

    Payment_Option = models.TextField(
        blank=True, null=True
    )

    copay = models.TextField(
        blank=True, null=True
    )

    copay_text = models.TextField(
        blank=True, null=True
    )

    copay_2 = models.TextField(
        blank=True, null=True
    )

    copay_2_text = models.CharField(
        max_length=1000,
        blank=True, null=True
    )


    # ------------------------------------------
    # stand alone ancillaries/add-on plan flag
    # ------------------------------------------
    stand_alone_addon_plan = models.BooleanField(
        default=False
    )

    note = models.TextField(
        blank=True, null=True
    )

    # enrolled = models.BooleanField(
    #     default=False
    # ) # TODO

    class Meta:
        db_table = 'main_plan'

    def __str__(self):
        return "{0}-{1}".format(self.vimm_enroll_id, getattr(self, 'plan_name_long', ''))

    def get_json_data(self):
        data = {
            'vimm_enroll_id': self.vimm_enroll_id,
            'Plan_ID': self.Plan_ID,
            'Name': self.Name,
            'Plan_Name': self.Plan_Name,
            'plan_name_for_img': self.plan_name_for_img,
            'plan_name': self.plan_name,
            'Plan': self.Plan,
            'ins_type': self.ins_type,
            'unique_url': self.unique_url,
            'Premium': str(self.Premium),
            'EnrollmentFee': str(self.EnrollmentFee),
            'Enrollment_Fee': str(self.Enrollment_Fee),
            'actual_premium': str(self.actual_premium),
            'quote_request_timestamp': self.quote_request_timestamp,
            'Quote_ID': self.Quote_ID,
            'Access_Token': self.Access_Token,
            'TelaDocFee': str(getattr(self, 'TelaDocFee', '0.0')),
            'TelaDoc_Fee': str(getattr(self, 'TelaDoc_Fee', '0.0')),
            'RxAdvocacyFee': str(getattr(self, 'RxAdvocacyFee', '0.0')),
            'RxAdvocacy_Fee': str(getattr(self, 'RxAdvocacy_Fee', '0.0')),
            'ChoiceValue_AdminFee': str(getattr(self, 'ChoiceValue_AdminFee', '0.0')),
            'ChoiceValueSavings_Fee': str(getattr(self, 'ChoiceValueSavings_Fee', '0.0')),
            'VBP_Fee': str(getattr(self, 'VBP_Fee', '0.0')),
            'Medsense_Fee': str(getattr(self, 'Medsense_Fee', '0.0')),
            'Association_Fee': str(getattr(self, 'Association_Fee', '0.0')),
            'product_id': self.Plan_ID,
            'premium': str(self.Premium),
            'Administrative_Fee': str(getattr(self, 'Administrative_Fee', '0.0')),
            'AdministrativeFee': str(getattr(self, 'AdministrativeFee', '0.0')),
            'RealValueSavings_Fee': str(self.RealValueSavings_Fee),
            'RealValueSavings_AdminFee': str(self.RealValueSavings_AdminFee),
            'month': self.month,
            'option': self.option,
            'Benefit_Amount': str(self.Benefit_Amount),
            'Coinsurance_Percentage': self.Coinsurance_Percentage,
            'out_of_pocket_value': str(self.out_of_pocket_value),
            'Duration_Coverage': self.Duration_Coverage,
            'Deductible_Option': self.Deductible_Option,
            'copay': self.copay,
            'copay_text': self.copay_text,
            'Payment_Option': self.Payment_Option,
            'note': self.note,
            'Coverage_Max': str(self.Coverage_Max)
        }

        return data


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
            ('AdvantHealth STM', 'AdvantHealth STM'),
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


# class StandAloneAddonPlan(models.Model):
#
#     stm_enroll = models.ForeignKey(
#         StmEnroll,
#         on_delete=models.CASCADE,
#         verbose_name=_("Enroll"),
#     )
#
#     vimm_enroll_id = models.CharField(
#         max_length=20,
#         unique=True,
#         db_index=True
#     )
#
#     Plan_ID = models.CharField(
#         verbose_name=_("Plan ID"),
#         max_length=600,
#         db_index=True
#     )
#
#     Plan_Type = models.CharField(
#         max_length=500,
#         choices=(
#             ('Single Member', 'Single Member'),
#             ('Member+1', 'Member+1'),
#             ('Family', 'Family'),
#
#         )
#     )
#
#     Name = models.CharField(
#         max_length=600,
#         db_index=True
#     )
#
#     Lim_Plan_Name = models.CharField(
#         max_length=200,
#         db_index=True
#     )
#
#     plan_name_for_img = models.CharField(
#         max_length=600,
#         db_index=True
#     )
#
#     plan_name = models.CharField(
#         max_length=600,
#         blank=True, null=True
#     )
#
#     unique_url = models.CharField(
#         max_length=700,
#         db_index=True,
#         blank=True, null=True
#     )
#
#     Premium = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     EnrollmentFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     Enrollment_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     Administrative_Fee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2,
#         blank=True, null=True
#
#     )
#
#     AdministrativeFee = models.DecimalField(
#         max_digits=20,
#         decimal_places=2,
#         blank=True, null=True
#
#     )
#
#     actual_premium = models.DecimalField(
#         max_digits=20,
#         decimal_places=2
#     )
#
#     Quote_ID = models.CharField(
#         max_length=600,
#         blank=True, null=True
#     )
#
#     Access_Token = models.CharField(
#         max_length=700,
#         blank=True, null=True
#     )
#
#     quote_request_timestamp = models.IntegerField(
#         blank=True, null=True
#     )
#
#     note = models.TextField(
#         blank=True, null=True
#     )
#
#     def get_json_data(self):
#         return {
#             'vimm_enroll_id': self.vimm_enroll_id,
#             'Plan_ID': self.Plan_ID,
#             'Name': self.Name,
#             'Lim_Plan_Name': self.Lim_Plan_Name,
#             'plan_name_for_img': self.plan_name_for_img,
#             'plan_name': self.plan_name,
#             'unique_url': self.unique_url,
#             'Premium': str(self.Premium),
#             'EnrollmentFee': str(self.EnrollmentFee),
#             'Enrollment_Fee': str(self.Enrollment_Fee),
#             'AdministrativeFee': str(self.AdministrativeFee),
#             'Administrative_Fee': str(self.Administrative_Fee),
#             'actual_premium': str(self.actual_premium),
#             'quote_request_timestamp': self.quote_request_timestamp,
#             'Quote_ID': self.Quote_ID,
#             'Access_Token': self.Access_Token,
#             'note': self.note
#         }
#
#     class Meta:
#         db_table = 'stand_alone_addon_plan'


class Feature(models.Model):
    plan = models.ForeignKey(
        "Carrier",
        on_delete=models.CASCADE,
    )

    plan_number = models.CharField(
        max_length=20,
        blank=True, null=True,
    )

    order_serial = models.IntegerField(default=0)

    title = models.CharField(
        max_length=200,
        blank=True, null=True,
    )

    description = RichTextField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} - {}({})".format(self.title, self.plan.name, self.plan_number) if self.title else "-"

    class Meta:
        ordering = ['plan', 'order_serial', 'plan_number']


class BenefitsAndCoverage(Feature):
    self_fk = models.ForeignKey(
        "BenefitsAndCoverage",
        on_delete=models.CASCADE,
        blank=True, null=True,
    )

    image = models.ImageField(
        verbose_name='Image File',
        upload_to=get_img_path_by_filename,
        blank=True,
        null=True,
    )

    feature_type = models.CharField(
        max_length=50,
        default="Benefits and Coverage",
        editable=False,
    )

    def get_instance(self):
        """hack to ignore many to many relation"""
        return self if self.title else self.self_fk


class RestrictionsAndOmissions(Feature):
    self_fk = models.ForeignKey(
        "RestrictionsAndOmissions",
        on_delete=models.CASCADE,
        blank=True, null=True,
    )

    feature_type = models.CharField(
        max_length=50,
        default="Disclaimers & Restrictions",
        editable=False,
    )

    def get_instance(self):
        """hack to ignore many to many relation"""
        return self if self.title else self.self_fk

