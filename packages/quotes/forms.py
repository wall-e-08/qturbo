from __future__ import unicode_literals, print_function

import re
import copy
import time
import string
import datetime

from django import forms
from django.conf import settings
from django.forms import BaseFormSet
from django.forms import formset_factory
from django.utils.translation import ugettext_lazy as _

from pycard import Card, ExpDate
from pyzipcode import ZipCodeDatabase
from ipware.ip import get_real_ip, get_ip

from .models import Leads
from .us_states import states
from .quote_response import AddonPlan
from .ssn import is_valid as is_valid_ssn, format as ssn_format
from .rtn import is_valid as is_valid_rtn
from .utils import (age, get_years_for_card, clean_number, validate_name,
                               get_askable_questions, get_plan_type_principle_limited)

QR_DATE_PATTERN = re.compile(r'^(\d{2})-(\d{2})-(\d{4})$')


class ZipCodeForm(forms.Form):

    zip_code = forms.CharField(
        label=_("Zip Code"),
        max_length=5,
        min_length=5,
        strip=True,
        error_messages={'required': _("Zip Code is required.")}
    )

    def clean_zip_code(self):
        zip_code = self.cleaned_data['zip_code']
        print(zip_code)
        for char in zip_code:
            if char not in string.digits:
                raise forms.ValidationError(_("Invalid zip code"))
        if len(zip_code) != 5:
            raise forms.ValidationError(_('Invalid zip code'))
        try:
            return ZipCodeDatabase()[zip_code]
        except IndexError:
            raise forms.ValidationError(_("Invalid zip code"))


class HealthCareZipCodeForm(forms.Form):

    Zip_Code = forms.CharField(
        label=_("Zip Code"),
        max_length=5,
        min_length=5,
        strip=True,
        error_messages={'required': _("Zip Code is required.")}
    )

    def clean_Zip_Code(self):
        zip_code = self.cleaned_data['Zip_Code']
        print(zip_code)
        for char in zip_code:
            if char not in string.digits:
                raise forms.ValidationError(_("Invalid zip code"))
        if len(zip_code) != 5:
            raise forms.ValidationError(_('Invalid zip code'))
        try:
            print(ZipCodeDatabase()[zip_code], type(ZipCodeDatabase()[zip_code]))
            return ZipCodeDatabase()[zip_code]
        except IndexError:
            raise forms.ValidationError(_("Invalid zip code"))


class ApplicantInfoForm(forms.Form):

    APPLICANT_MAX_AGE = 64
    APPLICANT_MIN_AGE = 2

    SPOUSE_AGE_LL = 18
    SPOUSE_AGE_UL = 64

    MIN_COVERAGE_DAYS = 30
    MAX_COVERAGE_DAYS = 337

    Ins_Type = forms.ChoiceField(
        label=_("Insurance Type"),
        choices=(
            ('stm', 'STM'),
            ('lim', 'Limited'),
            ('anc', 'Ancillary'),
        ),
        error_messages={"required": _("Insurance Type is required.")}
    )

    State = forms.ChoiceField(
        label=_("State"),
        choices=states,
        required=False
    )

    Zip_Code = forms.CharField(
        label=_("Zip Code"),
        max_length=5,
        min_length=5,
        strip=True,
        error_messages={'required': _("Zip Code is required.")}
    )

    First_Name = forms.CharField(
        label=_("First Name"),
        max_length=50,
        # error_messages={'required': _("First Name is required.")}
        required=False
    )

    Last_Name = forms.CharField(
        label=_("Last Name"),
        max_length=50,
        # error_messages={'required': _("Last Name is required.")}
        required=False
    )

    Address1=forms.CharField(
        label=_("Address1"),
        max_length=100,
        # error_messages={'required': _("Address is required.")}
        required=False
    )

    Email = forms.EmailField(
        label=_("Email"),
        max_length=75,
        # error_messages={'required': _("Email Address is required.")}
        required=False
    )

    Phone = forms.CharField(
        label=_("Phone"),
        # error_messages={'required': _("Phone Number is required.")}
        required=False
    )

    Applicant_Gender = forms.ChoiceField(
        label=_("Applicant Gender"),
        choices=(
            ("Male", _("Male")),
            ("Female", _("Female"))
        ),
        error_messages={"required": _("Applicant Gender is required.")},
        required=True
    )

    Applicant_DOB = forms.DateField(
        label=_("Date of Birth"),
        error_messages={"required": _("Applicant Date of Birth is required.")},
        required=True
    )

    Applicant_Age = forms.IntegerField(required=False)

    applicant_is_child = forms.BooleanField(required=False)

    Include_Spouse = forms.ChoiceField(
        choices=(
            ("Yes", _("Yes")),
            ("No", _("No"))
        ),
    )

    Spouse_Gender = forms.ChoiceField(
        choices=(
            ("Male", _("Male")),
            ("Female", _("Female"))
        ),
        required=False
    )

    Spouse_DOB = forms.DateField(required=False)

    Spouse_Age = forms.IntegerField(required=False)

    Children_Count = forms.IntegerField()

    Payment_Option = forms.ChoiceField(
        label=_("Payment Option"),
        choices=(
            (1, "Monthly"),
            (2, "Single Up-Front")
        )
    )

    Effective_Date = forms.DateField(
        label=_("Coverage Start"),
        error_messages={"required": _("Coverage Start Date is required.")}
    )

    Coverage_Days = forms.DateField(
        label=_("Coverage End"),
        required=False
    )

    Tobacco = forms.ChoiceField(
        label=_("Tobacco"),
        choices=(
            ("N", "No"),
            ("Y", "Yes"),
        )
    )

    Spouse_Tobacco = forms.ChoiceField(
        label=_("Spouse_Tobacco"),
        choices=(
            ("N", "No"),
            ("Y", "Yes"),
        ),
        required=False
    )

    Annual_Income = forms.CharField(
        label=_("Annual Income"),
        error_messages={'required': _("Annual Income is Required")},
        required=True
    )

    quote_request_timestamp = forms.IntegerField(required=False)

    def clean_First_Name(self):
        First_Name = self.cleaned_data.get('First_Name', '')
        if First_Name and not validate_name(First_Name):
            raise forms.ValidationError(
                "First Name allows only letters(a-z or A-Z), numbers(0-9), "
                "space( ), single quote('), underscore(_), dash(-) and periods(.).",
                code='invalid'
            )
        return First_Name

    def clean_Last_Name(self):
        Last_Name = self.cleaned_data.get('Last_Name', '')
        if Last_Name and not validate_name(Last_Name):
            raise forms.ValidationError(
                "Last Name allows only letters(a-z or A-Z), numbers(0-9), "
                "space( ), single quote('), underscore(_), dash(-) and periods(.).",
                code='invalid'
            )
        return Last_Name

    # def clean_Phone(self):
    #     phone = clean_number(self.cleaned_data.get('Phone', ''))
    #     if len(phone) != 10:
    #         raise forms.ValidationError("Invalid Phone Number", code='invalid')
    #     return phone[:3] + '-' + phone[3:6] + '-' + phone[6:]

    def clean_Zip_Code(self):
        zip_code = self.cleaned_data['Zip_Code']
        print(zip_code)
        for char in zip_code:
            if char not in string.digits:
                raise forms.ValidationError(_("Invalid zip code"))
        if len(zip_code) != 5:
            raise forms.ValidationError(_('Invalid zip code'))
        try:
            return ZipCodeDatabase()[zip_code]
        except IndexError:
            raise forms.ValidationError(_("Invalid zip code"))

    def clean_Children_Count(self):
        children_count = self.cleaned_data['Children_Count']
        if not (0 <= children_count <= 9):
            raise forms.ValidationError(_("Invalid number of dependents"), code='invalid')
        return children_count

    def clean_Applicant_DOB(self):
        dob = self.cleaned_data['Applicant_DOB']
        if dob > datetime.date.today():
            raise forms.ValidationError(_("Future Date is not a valid Date of Birth"), code='invalid')
        if age(dob) > self.APPLICANT_MAX_AGE:
            raise forms.ValidationError(_("Applicant maximum age is 64 years."), code='limit')
        if age(dob) < self.APPLICANT_MIN_AGE:
            raise forms.ValidationError(_("Applicant minimum age is 2 years."), code='limit')
        return dob.strftime("%m-%d-%Y")

    def clean_Spouse_DOB(self):
        spouse_dob = self.cleaned_data['Spouse_DOB']
        if isinstance(spouse_dob, datetime.date):
            if spouse_dob > datetime.date.today():
                raise forms.ValidationError(_("Future Date is not a valid Date of Birth"), code='invalid')
            if self.SPOUSE_AGE_LL > age(spouse_dob) > self.SPOUSE_AGE_UL:
                raise forms.ValidationError(_("Spouse age limit is between 16 to 64 years."), code='limit')
            return spouse_dob.strftime("%m-%d-%Y")
        return spouse_dob

    def clean_Effective_Date(self):
        effective_date = self.cleaned_data['Effective_Date']
        if effective_date < datetime.date.today():
            raise forms.ValidationError(_('Invalid Coverage Start Date.'), code='invalid')
        if effective_date.day > 28:
            raise forms.ValidationError(
                _("Invalid Coverage Start Date. Coverage Start Date must be 1-28th of any month."),
                code='invalid'
            )
        return effective_date.strftime("%m-%d-%Y")

    def clean_Coverage_Days(self):
        coverage_end = self.cleaned_data['Coverage_Days']
        if isinstance(coverage_end, datetime.date):
            return coverage_end.strftime("%m-%d-%Y")
        return coverage_end

    def clean(self):
        super().clean()

        zip_code = self.cleaned_data.get('Zip_Code', None)
        if zip_code is not None:
            self.cleaned_data['Zip_Code'] = zip_code.zip
            self.cleaned_data['State'] = zip_code.state

        applicant_dob = self.cleaned_data.get('Applicant_DOB', None)
        if applicant_dob:
            self.cleaned_data['Applicant_Age'] = self._process_dob_for_age(applicant_dob)
            if self.cleaned_data['Applicant_Age'] < 18:
                self.cleaned_data['applicant_is_child'] = True
                self.cleaned_data['Include_Spouse'] = 'No'
                self.cleaned_data['Children_Count'] = 0

        include_spouse = self.cleaned_data.get('Include_Spouse', None)
        if include_spouse == 'Yes':
            spouse_dob = self.cleaned_data.get('Spouse_DOB', None)
            if not spouse_dob:
                self.add_error(
                    'Spouse_DOB',
                    forms.ValidationError(_("Spouse Date of Birth is required."), code='required')
                )
            else:
                self.cleaned_data['Spouse_Age'] = self._process_dob_for_age(spouse_dob)
            spouse_gender = self.cleaned_data.get('Spouse_Gender', None)
            if not spouse_gender:
                self.add_error(
                    'Spouse_Gender',
                    forms.ValidationError(_("Spouse Gender is required."), code='required')
                )
            spouse_tobacco = self.cleaned_data.get('Spouse_Tobacco')
            if not spouse_tobacco:
                self.add_error(
                    'Spouse_Tobacco',
                    forms.ValidationError(_("Spouse_Tobacco is required."), code='required')
                )
            else:
                self.cleaned_data['Spouse_Tobacco'] = spouse_tobacco
        elif include_spouse == 'No':
            self.cleaned_data['Spouse_DOB'] = None
            self.cleaned_data['Spouse_Gender'] = ''

        payment_option = self.cleaned_data.get('Payment_Option', None)
        if str(payment_option) == '2':
            coverage_end = self.cleaned_data.get('Coverage_Days', None)
            effective_date = self.cleaned_data.get('Effective_Date', None)
            if coverage_end and isinstance(coverage_end, str):
                coverage_end = datetime.datetime.strptime(coverage_end, '%m-%d-%Y').date()
            if effective_date and isinstance(effective_date, str):
                effective_date = datetime.datetime.strptime(effective_date, '%m-%d-%Y').date()
            if effective_date and coverage_end:
                if not self.MIN_COVERAGE_DAYS <= (coverage_end - effective_date).days <= self.MAX_COVERAGE_DAYS:
                    self.add_error(
                        'Coverage_Days',
                        forms.ValidationError("Coverage Days must be between {0} to {1} days".format(
                            self.MIN_COVERAGE_DAYS,
                            self.MAX_COVERAGE_DAYS
                        ), code='limit')
                    )
            if not coverage_end:
                self.add_error(
                    'Coverage_Days',
                    forms.ValidationError(_("Coverage End is required"), code='required')
                )
        elif str(payment_option) == '1':
            self.cleaned_data['Coverage_Days'] = None

        tobacco = self.cleaned_data.get('Tobacco')
        if not tobacco:
            self.add_error(
                'Tobacco',
                forms.ValidationError(_("Tobacco is required."), code='required')
            )
        else:
            self.cleaned_data['Tobacco'] = tobacco


        self.cleaned_data['quote_request_timestamp'] = int(round(time.time(), 0))

        self.cleaned_data['Annual_Income'] = self.cleaned_data.get('Annual_Income', None)

        return self.cleaned_data

    def _process_dob_for_age(self, dob):
        if isinstance(dob, str):
            dob = datetime.datetime.strptime(dob, '%m-%d-%Y').date()
        return age(dob)


class Duration_Coverage_Form(forms.Form):
    Duration_Coverage = forms.ChoiceField(
        label=_("Select Minimum"),
        choices=(),
        error_messages={"required": _("Max out of pocket is required.")},
        required=False
    )

class Alt_Benefit_Amount_Coinsurance_Coverage_Maximum_Form(forms.Form):

    Benefit_Amount = forms.CharField(
        label=_("Select Max Out Of Pocket"),
        error_messages={"required": _("Max out of pocket is required.")},
        required=False
    )


    Coinsurance_Percentage = forms.CharField(
        label=_("Select Co-Insurance Percentage"),
        error_messages={"required": _("Co-Insurance Percentage required.")},
        required=False
    )

    Coverage_Max = forms.CharField(
        label=_("Select Maximum Amount of Coverage"),
        error_messages={"required": _("Coverage_Maximum is required.")},
        required=False
    )

    def clean(self):
        super().clean()

        benefit_amount = self.cleaned_data.get('Benefit_Amount', None)
        if benefit_amount is not None:
            self.cleaned_data['Benefit_Amount'] = benefit_amount

        coinsurance_percentage = self.cleaned_data.get('Coinsurance_Percentage', None)
        if coinsurance_percentage is not None:
            self.cleaned_data['Coinsurance_Percentage'] = coinsurance_percentage

        coverage_max = self.cleaned_data.get('Coverage_Max', None)
        if coverage_max is not None:
            self.cleaned_data['Coverage_Maximum'] = coverage_max

        return self.cleaned_data



class ChildInfoForm(forms.Form):

    MAX_CHILD_AGE = 25

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.empty_permitted = False

    Child_Gender = forms.ChoiceField(
        choices=(
            ("Male", _("Male")),
            ("Female", _("Female"))
        ),
        error_messages={'required': _("Child Gender is required.")}
    )

    Child_DOB = forms.DateField(
        error_messages={"required": _("Child Date of Birth is required.")}
    )

    Child_Age = forms.IntegerField(required=False)

    def clean_Child_DOB(self):
        dob = self.cleaned_data['Child_DOB']
        if dob > datetime.date.today():
            raise forms.ValidationError(_("Future Date is not a valid Date of Birth"), code='invalid')
        if self._process_dob_for_age(dob) > self.MAX_CHILD_AGE:
            raise forms.ValidationError(
                _("Child must not be older than {0}".format(self.MAX_CHILD_AGE)),
                code='invalid'
            )
        return dob.strftime("%m-%d-%Y")

    def clean(self):
        super().clean()
        dob = self.cleaned_data.get('Child_DOB', None)
        if dob:
            self.cleaned_data['Child_Age'] = self._process_dob_for_age(dob)
        return self.cleaned_data

    def _process_dob_for_age(self, dob):
        if isinstance(dob, str):
            dob = datetime.datetime.strptime(dob, '%m-%d-%Y').date()
        return age(dob)


class BaseChildFormSet(BaseFormSet):
    @classmethod
    def get_default_prefix(cls):
        return 'child'


ChildInfoFormSet = formset_factory(ChildInfoForm, formset=BaseChildFormSet, extra=0, max_num=9)


# STAGE ONE - QUESTION


class StageOneForm(forms.Form):

    REQUEST_FIELD = 'question_request_name'

    def __init__(self, request, stm_questions_key, stm_questions, *args, **kwargs):
        self.request = request
        self.stm_questions_key = stm_questions_key
        self.stm_questions = stm_questions
        self.stm_questions_values = sorted(stm_questions.values(), key=lambda x: x['order'])
        super().__init__(*args, **kwargs)

    question_request_name = forms.CharField(error_messages={"required": _("Question request name is required.")})

    total = forms.IntegerField(error_messages={"required": _("Total Question is required.")})

    def clean_question_request_name(self):
        question_request_name = self.cleaned_data.get('question_request_name', '').strip()
        if question_request_name != self.REQUEST_NAME:
            raise forms.ValidationError(_("Invalid Question Request Name."), code='invalid')
        return question_request_name

    def clean_total(self):
        total = self.cleaned_data.get('total', -1)
        if total != len(get_askable_questions(self.stm_questions.values())):
            raise forms.ValidationError(_('Invalid Total Question.'), code='invalid')
        return total


class QuestionForm(StageOneForm):

    REQUEST_NAME = ''

    order = forms.IntegerField(error_messages={"required": _("Question Order is required.")})

    def clean_order(self):
        order = self.cleaned_data.get('order', -1)
        if 0 > order >= len(get_askable_questions(self.stm_questions.values())):
            raise forms.ValidationError(_('Invalid Question Order.'), code='invalid')
        return order


class AppAnswerForm(QuestionForm):

    REQUEST_NAME = 'user_answer'

    answer = forms.CharField(error_messages={"required": _("Answer is required.")})

    question_id = forms.IntegerField(error_messages={"required": _("Question ID is required.")})

    is_correct_ans = forms.BooleanField(required=False)

    parent_id = forms.IntegerField(required=False)

    def clean(self):
        super().clean()
        answer = self.cleaned_data.get('answer', None)
        question_id = str(self.cleaned_data.get('question_id', ''))
        parent_id = str(self.cleaned_data.get('parent_id', '') or '')
        if parent_id:
            parent_question = self.stm_questions.get(parent_id, None)
            if parent_question:
                try:
                    stm_question = next(filter(lambda q: q['ID'] == question_id, parent_question['SubQue']))
                    self.sub_order = stm_question['sub_order']
                except StopIteration:
                    stm_question = None
            else:
                stm_question = None
        else:
            # print("NO PARENT")
            stm_question = self.stm_questions.get(question_id, None)

        if not stm_question:
            self.add_error('question_id', forms.ValidationError(_("Invalid Question ID"), code='invalid'))
        elif stm_question and answer:
            if answer not in stm_question['ExpectedAnswers']:
                self.add_error('answer', forms.ValidationError(_("Invalid Answer"), code='invalid'))
            elif answer != stm_question['CorrectAnswer']:
                self.cleaned_data['is_correct_ans'] = True
            else:
                self.cleaned_data['is_correct_ans'] = False

        return self.cleaned_data

    def save(self):
        if self.cleaned_data['parent_id']:
            self.request.session[self.stm_questions_key][
                str(self.cleaned_data['parent_id'])]['SubQue'][
                int(self.sub_order)]['user_answer'] = self.cleaned_data['answer']
        else:
            self.request.session[self.stm_questions_key][str(
                self.cleaned_data['question_id'])]['user_answer'] = self.cleaned_data['answer']
        self.request.session.modified = True
        return self.cleaned_data['is_correct_ans']


class AppAnswerCheckForm(QuestionForm):

    REQUEST_NAME = 'answer_check'

    any_wrong_answer = forms.BooleanField(required=False)

    all_questions_answered = forms.BooleanField(required=False)

    def clean_any_wrong_answer(self):
        try:
            next(filter(
                lambda q: q['user_answer'] is not None and q['user_answer'] == q['CorrectAnswer'],
                get_askable_questions(self.stm_questions_values)
            ))
        except StopIteration:
            return False
        return True

    def clean_all_questions_answered(self):
        try:
            next(filter(lambda q: q['user_answer'] is None, get_askable_questions(self.stm_questions_values)))
        except StopIteration:
            return True
        return False


class StageOneTransitionForm(StageOneForm):

    REQUEST_NAME = 'transition'

    STAGE = 1

    NEXT_STAGE = 2

    stage = forms.IntegerField()

    next_stage = forms.IntegerField()

    def clean_stage(self):
        stage = self.cleaned_data.get('stage', -1)
        if stage != self.STAGE:
            raise forms.ValidationError(_("Invalid Stage"), code='invalid')
        return stage

    def clean_next_stage(self):
        next_stage = self.cleaned_data.get('next_stage', -1)
        if next_stage != self.NEXT_STAGE:
            raise forms.ValidationError(_("Invalid Next Stage"), code='invalid')
        return next_stage

    def _any_wrong_answer(self):
        try:
            next(filter(
                lambda q: q['user_answer'] is not None and q['user_answer'] == q['CorrectAnswer'],
                get_askable_questions(self.stm_questions_values)
            ))
        except StopIteration:
            return False
        return True

    def _all_questions_answered(self):
        try:
            next(filter(lambda q: q['user_answer'] is None, get_askable_questions(self.stm_questions_values)))
        except StopIteration:
            return True
        return False

    def clean(self):
        super().clean()
        if self._any_wrong_answer():
            raise forms.ValidationError(_("Wrong answer found."), code='invalid')
        if not self._all_questions_answered():
            raise forms.ValidationError(_("All questions, not answered."), code='invalid')
        return self.cleaned_data


# STAGE TWO - APPLICANT INFO


class STParentInfo(forms.Form):

    MIN_AGE = 18

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    Parent_First_Name = forms.CharField(
        label=_("First Name"),
        max_length=50
    )

    Parent_Last_Name = forms.CharField(
        label=_("Last Name"),
        max_length=50
    )

    Parent_Gender = forms.ChoiceField(
        label=_("Gender"),
        choices=(
            ("Male", _("Male")),
            ("Female", _("Female"))
        )
    )

    Parent_DOB = forms.DateField(label=_("Date of Birth"))

    Parent_Email = forms.EmailField(
        label=_("Email"),
        max_length=75,
    )

    Parent_DayPhone = forms.CharField(label=_("Phone Number"))

    Parent_CellPhone = forms.CharField(label=_("Alternate Phone Number"))

    # must be taken from applicant contact info
    Parent_Address = forms.CharField(required=False)

    Parent_City = forms.CharField(required=False)

    Parent_State = forms.ChoiceField(required=False, choices=states)

    Parent_ZipCode = forms.CharField(
        required=False
    )

    def clean_Parent_ZipCode(self):
        zip_code = self.cleaned_data.get('Parent_ZipCode')
        if not zip_code:
            return None
        for char in zip_code:
            if char not in string.digits:
                raise forms.ValidationError(_("Invalid zip code"))
        if len(zip_code) != 5:
            raise forms.ValidationError(_('Invalid zip code'))
        try:
            ZipCodeDatabase()[zip_code]
        except IndexError:
            raise forms.ValidationError(_("Invalid zip code"))
        return zip_code

    def clean_Parent_DOB(self):
        dob = self.cleaned_data['Parent_DOB']
        if dob > datetime.date.today():
            raise forms.ValidationError(_("Future Date is not a valid Date of Birth"), code='invalid')
        if age(dob) < self.MIN_AGE:
            raise forms.ValidationError(_("Parent minimum age is 18 years."), code='limit')
        return dob.strftime("%Y-%m-%d")

    # def clean_Parent_DayPhone(self):
    #     phone = clean_number(self.cleaned_data.get('Parent_DayPhone', ''))
    #     if len(phone) != 10:
    #         raise forms.ValidationError("Invalid Phone Number", code='invalid')
    #     return phone[:3] + '-' + phone[3:6] + '-' + phone[6:]
    #
    # def clean_Parent_CellPhone(self):
    #     phone = clean_number(self.cleaned_data.get('Parent_CellPhone', ''))
    #     if len(phone) != 10:
    #         raise forms.ValidationError("Invalid Phone Number", code='invalid')
    #     return phone[:3] + '-' + phone[3:6] + '-' + phone[6:]

    def clean(self):
        super().clean()
        applicant_data = self.initial if self.initial else {}
        for field in ['Parent_Address', 'Parent_City', 'Parent_State', 'Parent_ZipCode']:
            self.cleaned_data[field] = applicant_data.get(field.replace('Parent_', ''), '')

        first_name = self.cleaned_data.get('Parent_First_Name', '')
        last_name = self.cleaned_data.get('Parent_Last_Name', '')
        self.cleaned_data['Name_Enroll'] = "{0} {1}".format(first_name, last_name)[:75]
        self.cleaned_data['Name_Auth'] = "{0} {1}".format(first_name, last_name)[:75]
        return self.cleaned_data


class STApplicantInfoForm(forms.Form):

    APPLICANT_MAX_AGE = 64

    APPLICANT_MIN_AGE = 2

    def __init__(self, initial_form_data, plan, request, initialize_form=None, *args, **kwargs):
        self.initial_form_data = initial_form_data
        self.request = request
        self.plan = plan
        self.initialize_form = initialize_form
        self.mailing_state_from_zip_code = None
        if self.initialize_form:
            super().__init__(initial={
                "First_Name": self.initial_form_data.get("First_Name"),
                "Last_Name": self.initial_form_data.get("Last_Name"),
                "Email": self.initial_form_data.get("Email"),
                "DayPhone": self.initial_form_data.get("Phone"),
                "CellPhone": self.initial_form_data.get("Phone"),
                "DOB": QR_DATE_PATTERN.sub(r'\3-\1-\2', self.initial_form_data["Applicant_DOB"]),
                "Applicant_is_Child": self.initial_form_data.get("applicant_is_child"),
                "Address": self.initial_form_data.get("Address1"),
                'Gender': self.initial_form_data["Applicant_Gender"],
                "State": self.initial_form_data["State"],
                "ZipCode": self.initial_form_data["Zip_Code"],
                "Mailing_State": self.initial_form_data["State"],
                "Mailing_ZipCode": self.initial_form_data["Zip_Code"],
                "Tobacco": self.initial_form_data["Tobacco"]
            }, *args, **kwargs)
        else:
            super().__init__(*args, **kwargs)

    First_Name = forms.CharField(
        label=_("First Name"),
        max_length=50,
        error_messages={"required": _("Applicant First Name is required.")}
    )

    Middle_Name = forms.CharField(
        label=_("Middle Name"),
        max_length=50,
        required=False
    )

    Last_Name = forms.CharField(
        label=_("Last Name"),
        max_length=50,
        error_messages={"required": _("Applicant Last Name is required.")}
    )

    Gender = forms.ChoiceField(
        choices=(
            ("Male", _("Male")),
            ("Female", _("Female"))
        ),
        label=_("Gender"),
        required=False
    )

    DOB = forms.DateField(
        label=_("Date of Birth"),
        required=False
    )

    Applicant_is_Child = forms.BooleanField(required=False)

    Tobacco = forms.ChoiceField(
        required=False,
        label=_("Tobacco"),
        choices=(
            ("N", "No"),
            ("Y", "Yes"),
        )
    )
    # only for Select STM + Cardinal Choice
    Occupation = forms.CharField(
        label=_("Occupation"),
        max_length=50,
        required=False,
        error_messages={"required": _("Occupation is required.")}
    )

    # only for Premier STM
    SOC = forms.CharField(required=False, label=_('Social Security Number'))

    Age = forms.IntegerField(
        label=_('Age'),
        required=False
    )

    Feet = forms.ChoiceField(
        label=_("Feet"),
        choices=(('2', '2'), ('3', '3'), ('4', '4'),
                 ('5', '5'), ('6', '6'), ('7', '7')),
        required=False,
        error_messages={"required": _("Height Feet is required.")}
    )

    Inch = forms.ChoiceField(
        label=_("Inch"),
        choices=(('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'),
                 ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'), ('11', '11')),
        required=False,
        error_messages={"required": _("Height Inch is required.")}
    )

    Weight = forms.IntegerField(
        label=_("Weight"),
        required=False,
        error_messages={"required": _("Weight is required.")}
    )

    Address = forms.CharField(
        label=_("Address"),
        error_messages={"required": _("Applicant Address is required.")}
    )

    City = forms.CharField(
        label=_("City"),
        max_length=50,
        error_messages={"required": _("Applicant City is required.")}
    )

    State = forms.ChoiceField(
        choices=states,
        label=_("State"),
        error_messages={"required": _("Applicant State is required.")}
    )

    ZipCode = forms.CharField(
        label=_("Zip Code"),
        error_messages={'required': _("Zip Code is required.")}
    )

    Email = forms.EmailField(
        label=_("Email"),
        max_length=75,
        error_messages={'required': _("Email Address is required.")}
    )

    DayPhone = forms.CharField(
        label=_("Phone Number"),
        error_messages={'required': _("Phone Number is required.")}
    )

    CellPhone = forms.CharField(
        label=_("Alternate Phone Number"),
        error_messages={'required': _("Alternate Phone Number is required.")}
    )

    mailing_not_as_contact = forms.BooleanField(required=False, initial=False)

    # mailing address
    Mailing_Name = forms.CharField(
        required=False,
        label=_("Name"),
        max_length=75
    )

    Mailing_Address = forms.CharField(
        required=False,
        label=_("Address"),
        max_length=100
    )

    Mailing_City = forms.CharField(
        required=False,
        label=_("City"),
        max_length=50
    )

    Mailing_State = forms.ChoiceField(
        choices=states,
        required=False,
        label=_("State")
    )

    Mailing_ZipCode = forms.CharField(
        required=False,
        label=_("Zip Code")
    )

    Effective_Date = forms.DateField(required=False)

    def clean_Mailing_ZipCode(self):
        zip_code = self.cleaned_data.get('Mailing_ZipCode')
        if not zip_code:
            return None
        for char in zip_code:
            if char not in string.digits:
                raise forms.ValidationError(_("Invalid zip code"))
        if len(zip_code) != 5:
            raise forms.ValidationError(_('Invalid zip code'))
        try:
            db_zip = ZipCodeDatabase()[zip_code]
            self.mailing_state_from_zip_code = db_zip.state
        except IndexError:
            raise forms.ValidationError(_("Invalid zip code"))
        return zip_code

    def clean_Weight(self):
        weight = self.cleaned_data.get('Weight')
        if weight is not None and not (1 <= weight <= 400):
            raise forms.ValidationError(_("Weight must be between 1 to 400 lbs."), code='invalid')
        return weight


    # def clean_DayPhone(self):
    #     phone = clean_number(self.cleaned_data.get('DayPhone', ''))
    #     if len(phone) != 10:
    #         raise forms.ValidationError("Invalid Phone Number", code='invalid')
    #     return phone[:3] + '-' + phone[3:6] + '-' + phone[6:]
    #
    # def clean_CellPhone(self):
    #     phone = clean_number(self.cleaned_data.get('CellPhone', ''))
    #     if len(phone) != 10:
    #         raise forms.ValidationError("Invalid Phone Number", code='invalid')
    #     return phone[:3] + '-' + phone[3:6] + '-' + phone[6:]

    def clean(self):
        super().clean()
        self.cleaned_data['Age'] = self.initial_form_data['Applicant_Age']
        self.cleaned_data['Gender'] = self.initial_form_data['Applicant_Gender']
        self.cleaned_data['Applicant_is_Child'] = self.initial_form_data['applicant_is_child']
        self.cleaned_data['Tobacco'] = self.initial_form_data['Tobacco']
        self.cleaned_data['DOB'] = QR_DATE_PATTERN.sub(r'\3-\1-\2', self.initial_form_data["Applicant_DOB"])

        mailing_not_as_contact = self.cleaned_data.get('mailing_not_as_contact', False)
        if mailing_not_as_contact:
            for field in ['Mailing_Name', 'Mailing_Address', 'Mailing_City', 'Mailing_State', 'Mailing_ZipCode']:
                if not self.cleaned_data.get(field):
                    self.add_error(
                        field,
                        forms.ValidationError("{0} is required.".format(field.replace('_', ' ')), code='required')
                    )
        else:
            for field in ['Mailing_Name', 'Mailing_Address', 'Mailing_City', 'Mailing_State', 'Mailing_ZipCode']:
                if field == 'Mailing_Name':
                    self.cleaned_data[field] = '{0} {1}'.format(self.cleaned_data.get('First_Name', ''),
                                                                self.cleaned_data.get('Last_Name', '')).strip()
                else:
                    self.cleaned_data[field] = self.cleaned_data.get(field.replace('Mailing_', ''), '')

        if (self.mailing_state_from_zip_code and self.cleaned_data.get('Mailing_ZipCode') and
                self.cleaned_data.get('Mailing_State')):
            if self.mailing_state_from_zip_code != self.cleaned_data.get('Mailing_State'):
                self.add_error(
                    'Mailing_ZipCode',
                    forms.ValidationError("Invalid Zip Code for State {0}".format(
                        self.cleaned_data.get('Mailing_State')
                    ))
                )

        self.cleaned_data['Effective_Date'] = QR_DATE_PATTERN.sub(r'\3-\1-\2', self.initial_form_data['Effective_Date'])
        self.cleaned_data['EffectiveDate_Ack'] = 'Agree'
        self.cleaned_data['Access_Token'] = self.plan['Access_Token']
        self.cleaned_data['Quote_ID'] = self.plan['Quote_ID']

        # I think Lifeshield does not require this #TODO
        if self.plan['Name'] not in ['Principle Advantage', 'Cardinal Choice', 'Vitala Care',
                                     'Health Choice', 'Legion Limited Medical', 'Foundation Dental',
                                     'USA Dental', 'Safeguard Critical Illness', 'Freedom Spirit Plus']:
            for field in ['Feet', 'Inch', 'Weight']:
                if not self.cleaned_data.get(field):
                    self.add_error(
                        field,
                        forms.ValidationError("{0} is required.".format(field), code='required')
                    )

        if self.plan['Name'] == 'Premier STM':
            soc = self.cleaned_data.get('SOC', '')
            if soc and not is_valid_ssn(soc):
                self.add_error('SOC', forms.ValidationError(_("Invalid Social Security Number."), code='invalid'))
            elif not soc:
                self.add_error('SOC', forms.ValidationError(_("Social Security Number is required."), code='required'))
            else:
                self.cleaned_data['SOC'] = ssn_format(soc)

            for field in ['Premium', 'Deductible_Option', 'Enrollment_Fee', 'Administrative_Fee',
                          'GapAffordPlus_Fee', 'GapAffordPlus_AdminFee', 'Duration_Coverage']:
                self.cleaned_data[field] = self.plan[field]
            for field in ['Beneficiary_First_Name', 'Beneficiary_Last_Name', 'Beneficiary_Relationship',
                          'Contingent_First_Name', 'Contingent_Last_Name', 'Contingent_Relationship']:
                self.cleaned_data[field] = ''
            for field in ['Payment_Agree', 'FraudNotice_Agree', 'CAUSA_Agree', 'Agile_Agree']:
                self.cleaned_data[field] = '1'
            self.cleaned_data['Estate_Flag'] = '1'
            self.cleaned_data['Estate_Detail'] = 'ESTATE'

        if self.plan['Name'] in ['HealtheMed STM', 'HealtheFlex STM']:
            for field in ['Premium', 'Deductible_Option', 'Enrollment_Fee', 'Administrative_Fee',
                          'Duration_Coverage', 'Payment_Option']:
                self.cleaned_data[field] = self.plan[field]
            self.cleaned_data['Coinsurance_Limit'] = "${0:,}".format(int(self.plan['Coinsurance_Limit']))
            self.cleaned_data['Coinsurance_Percentage'] = "{1}_{0}".format(
                self.plan['Coinsurance_Percentage'], 100 - int(self.plan['Coinsurance_Percentage']))

            self.cleaned_data['ESign_Option'] = 'Y'
            self.cleaned_data['ESign_Send_Method'] = 'Email'
            self.cleaned_data['Estate_Flag'] = '1'
            self.cleaned_data['Estate_Detail'] = 'ESTATE'

        if self.plan['Name'] == 'Sage STM':
            for field in ['Premium', 'Deductible_Option', 'Enrollment_Fee', 'Administrative_Fee',
                          'Duration_Coverage', 'Payment_Option']:
                self.cleaned_data[field] = self.plan[field]
            self.cleaned_data['Coinsurance_Limit'] = "${0:,}".format(int(self.plan['Coinsurance_Limit']))
            self.cleaned_data['Coinsurance_Percentage'] = "{1}/{0}".format(
                self.plan['Coinsurance_Percentage'], 100 - int(self.plan['Coinsurance_Percentage']))

            self.cleaned_data['ESign_Option'] = 'Y'
            self.cleaned_data['ESign_Send_Method'] = 'Email'
            self.cleaned_data['Estate_Flag'] = '1'
            self.cleaned_data['Estate_Detail'] = 'ESTATE'

        if self.plan['Name'] == 'Everest STM':
            for field in ['Premium', 'Deductible_Option', 'Coverage_Max', 'Plan_Name',
                          'Duration_Coverage', 'Payment_Option', 'Benefit_Amount',
                          'TelaDoc_Fee', 'Medsense_Fee', 'RxAdvocacy_Fee', 'Enrollment_Fee',
                          'ChoiceValueSavings_Fee', 'ChoiceValue_AdminFee', 'VBP_Fee']:
                self.cleaned_data[field] = self.plan[field]
            self.cleaned_data['Pre_Ex_Rider'] = 'N'
            self.cleaned_data['Coinsurance_Percentage'] = "{1}/{0}".format(
                self.plan['Coinsurance_Percentage'], 100 - int(self.plan['Coinsurance_Percentage']))

            self.cleaned_data['ESign_Option'] = 'Y'
            self.cleaned_data['ESign_Send_Method'] = 'Email'
            self.cleaned_data['Estate_Flag'] = '1'
            self.cleaned_data['Estate_Detail'] = 'ESTATE'

        if self.plan['Name'] == 'LifeShield STM':
            for field in ['Premium', 'Deductible_Option', 'Coverage_Max', 'Plan_Name',
                          'Duration_Coverage', 'Payment_Option', 'Benefit_Amount',
                          'TelaDoc_Fee', 'Medsense_Fee', 'RxAdvocacy_Fee', 'Enrollment_Fee',
                          'ChoiceValueSavings_Fee', 'ChoiceValue_AdminFee',
                          'RealValueSavings_Fee', 'RealValueSavings_AdminFee',
                          'VBP_Fee']:
                self.cleaned_data[field] = self.plan[field]
            self.cleaned_data['Pre_Ex_Rider'] = 'N'
            self.cleaned_data['Coinsurance_Percentage'] = "{1}/{0}".format(
                self.plan['Coinsurance_Percentage'], 100 - int(self.plan['Coinsurance_Percentage']))

            self.cleaned_data['ESign_Option'] = 'Y'
            self.cleaned_data['ESign_Send_Method'] = 'Email'
            self.cleaned_data['Estate_Flag'] = '1'
            self.cleaned_data['Estate_Detail'] = 'ESTATE'

        if self.plan['Name'] == 'AdvantHealth STM':
            for field in ['Premium', 'Deductible_Option', 'Coverage_Max', 'Plan_Name',
                          'Duration_Coverage', 'Payment_Option', 'Benefit_Amount',
                          'TelaDoc_Fee', 'Medsense_Fee', 'RxAdvocacy_Fee', 'Enrollment_Fee',
                          'ChoiceValueSavings_Fee', 'ChoiceValue_AdminFee',
                          'RealValueSavings_Fee', 'RealValueSavings_AdminFee',
                          'VBP_Fee', 'Association_Fee']:
                self.cleaned_data[field] = self.plan[field]
            self.cleaned_data['Pre_Ex_Rider'] = 'N'
            self.cleaned_data['Coinsurance_Percentage'] = "{1}/{0}".format(
                self.plan['Coinsurance_Percentage'], 100 - int(self.plan['Coinsurance_Percentage']))

            self.cleaned_data['ESign_Option'] = 'Y'
            self.cleaned_data['ESign_Send_Method'] = 'Email'
            self.cleaned_data['Estate_Flag'] = '1'
            self.cleaned_data['Estate_Detail'] = 'ESTATE'


        if self.plan['Name'] == 'Unified Health One':
            soc = self.cleaned_data.get('SOC', '') or '123456789'
            if soc and not is_valid_ssn(soc):
                self.add_error('SOC', forms.ValidationError(_("Invalid Social Security Number."), code='invalid'))
            elif not soc:
                self.add_error('SOC', forms.ValidationError(_("Social Security Number is required."), code='required'))
            else:
                self.cleaned_data['SOC'] = ssn_format(soc)
            for field in ['Premium', 'Enrollment_Fee', 'Administrative_Fee']:
                self.cleaned_data[field] = self.plan[field]
            self.cleaned_data['Plan_Name'] = self.plan['Lim_Plan_Name']
            for field in ['Beneficiary_First_Name', 'Beneficiary_Last_Name', 'Beneficiary_Relationship',
                          'Contingent_First_Name', 'Contingent_Last_Name', 'Contingent_Relationship']:
                self.cleaned_data[field] = ''
            self.cleaned_data['Estate_Flag'] = '1'
            self.cleaned_data['Estate_Detail'] = 'ESTATE'
            self.cleaned_data['Payment_Agree'] = '1'

        if self.plan['Name'] == 'Principle Advantage':
            for field in ['Premium', 'Enrollment_Fee', 'TelaDoc_Fee']:
                self.cleaned_data[field] = self.plan[field]
            self.cleaned_data['Plan_Name'] = self.plan['Lim_Plan_Name']
            self.cleaned_data['Plan_Type'] = get_plan_type_principle_limited(copy.deepcopy(self.initial_form_data))
            for field in ['Beneficiary_First_Name', 'Beneficiary_Last_Name', 'Beneficiary_Relationship',
                          'Contingent_First_Name', 'Contingent_Last_Name', 'Contingent_Relationship']:
                self.cleaned_data[field] = ''
            self.cleaned_data['Estate_Flag'] = '1'
            self.cleaned_data['Estate_Detail'] = 'ESTATE'
            self.cleaned_data['Payment_Agree'] = '1'

        if self.plan['Name'] == 'Cardinal Choice':
            # if not self.cleaned_data.get('Occupation', None):
            #     self.add_error(
            #         'Occupation',
            #         forms.ValidationError('Occupation is required', code='required')
            #     )
            for field in ['Premium', 'Enrollment_Fee', 'TelaDoc_Fee', 'RxAdvocacy_Fee',
                          'ChoiceValueSavings_Fee', 'ChoiceValue_AdminFee',
                          'RealValueSavings_Fee', 'RealValueSavings_AdminFee']:
                self.cleaned_data[field] = self.plan[field]
            self.cleaned_data['Plan_Name'] = self.plan['Lim_Plan_Name']

            beneficiary = ''
            for field in ['Beneficiary_First_Name', 'Beneficiary_Last_Name', 'Beneficiary_Relationship']:
                beneficiary += self.cleaned_data.get(field, '')
            if beneficiary:
                for field in ['Beneficiary_First_Name', 'Beneficiary_Last_Name', 'Beneficiary_Relationship']:
                    if not self.cleaned_data.get(field, ''):
                        self.add_error(
                            field,
                            "{0} is required".format(field.replace('_', ' '))
                        )
            contingent = ''
            for field in ['Contingent_First_Name', 'Contingent_Last_Name', 'Contingent_Relationship']:
                contingent += self.cleaned_data.get(field, '')
            if contingent:
                for field in ['Contingent_First_Name', 'Contingent_Last_Name', 'Contingent_Relationship']:
                    if not self.cleaned_data.get(field, ''):
                        self.add_error(
                            field,
                            "{0} is required".format(field.replace('_', ' '))
                        )
            if not (beneficiary and contingent):
                # for field in ['Beneficiary_First_Name', 'Beneficiary_Last_Name', 'Beneficiary_Relationship',
                #               'Contingent_First_Name', 'Contingent_Last_Name', 'Contingent_Relationship']:
                #     self.cleaned_data[field] = ''
                self.cleaned_data['Estate_Flag'] = '1'
                self.cleaned_data['Estate_Detail'] = 'ESTATE'
            else:
                self.cleaned_data['Estate_Flag'] = '0'
                self.cleaned_data['Estate_Detail'] = ''
            self.cleaned_data['ESign_Option'] = 'Y'
            self.cleaned_data['ESign_Send_Method'] = 'Email'
            self.cleaned_data['Payment_Agree'] = '1'

        if self.plan['Name'] == 'Vitala Care':
            # if not self.cleaned_data.get('Occupation', None):
            #     self.add_error(
            #         'Occupation',
            #         forms.ValidationError('Occupation is required', code='required')
            #     )
            for field in ['Premium', 'Enrollment_Fee', 'TelaDoc_Fee', 'RxAdvocacy_Fee',
                          'ChoiceValueSavings_Fee', 'ChoiceValue_AdminFee']:
                self.cleaned_data[field] = self.plan[field]
            self.cleaned_data['Plan_Name'] = self.plan['Lim_Plan_Name']

            beneficiary = ''
            for field in ['Beneficiary_First_Name', 'Beneficiary_Last_Name', 'Beneficiary_Relationship']:
                beneficiary += self.cleaned_data.get(field, '')
            if beneficiary:
                for field in ['Beneficiary_First_Name', 'Beneficiary_Last_Name', 'Beneficiary_Relationship']:
                    if not self.cleaned_data.get(field, ''):
                        self.add_error(
                            field,
                            "{0} is required".format(field.replace('_', ' '))
                        )
            contingent = ''
            for field in ['Contingent_First_Name', 'Contingent_Last_Name', 'Contingent_Relationship']:
                contingent += self.cleaned_data.get(field, '')
            if contingent:
                for field in ['Contingent_First_Name', 'Contingent_Last_Name', 'Contingent_Relationship']:
                    if not self.cleaned_data.get(field, ''):
                        self.add_error(
                            field,
                            "{0} is required".format(field.replace('_', ' '))
                        )
            if not (beneficiary and contingent):
                # for field in ['Beneficiary_First_Name', 'Beneficiary_Last_Name', 'Beneficiary_Relationship',
                #               'Contingent_First_Name', 'Contingent_Last_Name', 'Contingent_Relationship']:
                #     self.cleaned_data[field] = ''
                self.cleaned_data['Estate_Flag'] = '1'
                self.cleaned_data['Estate_Detail'] = 'ESTATE'
            else:
                self.cleaned_data['Estate_Flag'] = '0'
                self.cleaned_data['Estate_Detail'] = ''
            self.cleaned_data['ESign_Option'] = 'Y'
            self.cleaned_data['ESign_Send_Method'] = 'Email'
            self.cleaned_data['Payment_Agree'] = '1'

        if self.plan['Name'] == 'Health Choice':
            # if not self.cleaned_data.get('Occupation', None):
            #     self.add_error(
            #         'Occupation',
            #         forms.ValidationError('Occupation is required', code='required')
            #     )
            for field in ['Premium', 'Enrollment_Fee', 'TelaDoc_Fee', 'RxAdvocacy_Fee',
                          'ChoiceValueSavings_Fee', 'ChoiceValue_AdminFee']:
                self.cleaned_data[field] = self.plan[field]
            self.cleaned_data['Plan_Name'] = self.plan['Lim_Plan_Name']

            beneficiary = ''
            for field in ['Beneficiary_First_Name', 'Beneficiary_Last_Name', 'Beneficiary_Relationship']:
                beneficiary += self.cleaned_data.get(field, '')
            if beneficiary:
                for field in ['Beneficiary_First_Name', 'Beneficiary_Last_Name', 'Beneficiary_Relationship']:
                    if not self.cleaned_data.get(field, ''):
                        self.add_error(
                            field,
                            "{0} is required".format(field.replace('_', ' '))
                        )
            contingent = ''
            for field in ['Contingent_First_Name', 'Contingent_Last_Name', 'Contingent_Relationship']:
                contingent += self.cleaned_data.get(field, '')
            if contingent:
                for field in ['Contingent_First_Name', 'Contingent_Last_Name', 'Contingent_Relationship']:
                    if not self.cleaned_data.get(field, ''):
                        self.add_error(
                            field,
                            "{0} is required".format(field.replace('_', ' '))
                        )
            if not (beneficiary and contingent):
                # for field in ['Beneficiary_First_Name', 'Beneficiary_Last_Name', 'Beneficiary_Relationship',
                #               'Contingent_First_Name', 'Contingent_Last_Name', 'Contingent_Relationship']:
                #     self.cleaned_data[field] = ''
                self.cleaned_data['Estate_Flag'] = '1'
                self.cleaned_data['Estate_Detail'] = 'ESTATE'
            else:
                self.cleaned_data['Estate_Flag'] = '0'
                self.cleaned_data['Estate_Detail'] = ''

            # 'B' for voice verification
            # 'E' for direct verification
            # self.cleaned_data['ESign_Option'] = 'B'
            self.cleaned_data['ESign_Option'] = 'Y'
            self.cleaned_data['ESign_Send_Method'] = 'Email'
            self.cleaned_data['Payment_Agree'] = '1'

        if self.plan['Name'] == 'Legion Limited Medical':
            for field in ['Premium', 'Enrollment_Fee', 'TelaDoc_Fee', 'RxAdvocacy_Fee',
                          'ChoiceValueSavings_Fee', 'ChoiceValue_AdminFee']:
                self.cleaned_data[field] = self.plan[field]
            self.cleaned_data['Plan_Name'] = self.plan['Lim_Plan_Name']

            beneficiary = ''
            for field in ['Beneficiary_First_Name', 'Beneficiary_Last_Name', 'Beneficiary_Relationship']:
                beneficiary += self.cleaned_data.get(field, '')
            if beneficiary:
                for field in ['Beneficiary_First_Name', 'Beneficiary_Last_Name', 'Beneficiary_Relationship']:
                    if not self.cleaned_data.get(field, ''):
                        self.add_error(
                            field,
                            "{0} is required".format(field.replace('_', ' '))
                        )
            contingent = ''
            for field in ['Contingent_First_Name', 'Contingent_Last_Name', 'Contingent_Relationship']:
                contingent += self.cleaned_data.get(field, '')
            if contingent:
                for field in ['Contingent_First_Name', 'Contingent_Last_Name', 'Contingent_Relationship']:
                    if not self.cleaned_data.get(field, ''):
                        self.add_error(
                            field,
                            "{0} is required".format(field.replace('_', ' '))
                        )
            if not (beneficiary and contingent):
                # for field in ['Beneficiary_First_Name', 'Beneficiary_Last_Name', 'Beneficiary_Relationship',
                #               'Contingent_First_Name', 'Contingent_Last_Name', 'Contingent_Relationship']:
                #     self.cleaned_data[field] = ''
                self.cleaned_data['Estate_Flag'] = '1'
                self.cleaned_data['Estate_Detail'] = 'ESTATE'
            else:
                self.cleaned_data['Estate_Flag'] = '0'
                self.cleaned_data['Estate_Detail'] = ''

            # 'B' for voice verification
            # 'E' for direct verification
            # self.cleaned_data['ESign_Option'] = 'B'
            self.cleaned_data['ESign_Option'] = 'Y'
            self.cleaned_data['ESign_Send_Method'] = 'Email'
            self.cleaned_data['Payment_Agree'] = '1'

        if self.plan['Name'] == 'USA Dental':
            for field in ['Premium', 'Enrollment_Fee']: # Administrative_Fee is included in Premium
                self.cleaned_data[field] = self.plan[field]
            self.cleaned_data['Plan_Name'] = self.plan['Lim_Plan_Name']

            self.cleaned_data['Payment_Agree'] = '1'
            self.cleaned_data['Applicant_Agree'] = '1'
            self.cleaned_data['FraudNotice_Agree'] = '1'
            self.cleaned_data['Member_Agree'] = '1'

        if self.plan['Name'] == 'Foundation Dental':

            for field in ['Premium', 'Enrollment_Fee', 'Administrative_Fee']:
                self.cleaned_data[field] = self.plan[field]
            self.cleaned_data['Plan_Name'] = self.plan['Lim_Plan_Name']

            self.cleaned_data['Payment_Agree'] = '1'
            self.cleaned_data['Medsense_Agree'] = '1'
            self.cleaned_data['FraudNotice_Agree'] = '1'
            self.cleaned_data['Careington_Agree'] = '1'

        if self.plan['Name'] == 'Safeguard Critical Illness':

            for field in ['Premium', 'Enrollment_Fee', 'Administrative_Fee']:
                self.cleaned_data[field] = self.plan[field]
            self.cleaned_data['Plan_Name'] = self.plan['Lim_Plan_Name']

            beneficiary = ''
            for field in ['Beneficiary_First_Name', 'Beneficiary_Last_Name', 'Beneficiary_Relationship']:
                beneficiary += self.cleaned_data.get(field, '').strip()
            if beneficiary:
                for field in ['Beneficiary_First_Name', 'Beneficiary_Last_Name', 'Beneficiary_Relationship']:
                    if not self.cleaned_data.get(field, ''):
                        self.add_error(
                            field,
                            "{0} is required".format(field.replace('_', ' '))
                        )
            contingent = ''
            for field in ['Contingent_First_Name', 'Contingent_Last_Name', 'Contingent_Relationship']:
                contingent += self.cleaned_data.get(field, '').strip()
            if contingent:
                for field in ['Contingent_First_Name', 'Contingent_Last_Name', 'Contingent_Relationship']:
                    if not self.cleaned_data.get(field, ''):
                        self.add_error(
                            field,
                            "{0} is required".format(field.replace('_', ' '))
                        )
            if not (beneficiary and contingent):
                self.cleaned_data['Estate_Flag'] = '1'
                self.cleaned_data['Estate_Detail'] = 'ESTATE'
            else:
                self.cleaned_data['Estate_Flag'] = '0'
                self.cleaned_data['Estate_Detail'] = ''

            self.cleaned_data['Payment_Agree'] = '1'

        if self.plan['Name'] == 'Freedom Spirit Plus':
            ''' Put in here what is needed in xml '''


            for field in ['Premium', 'Enrollment_Fee', 'Administrative_Fee']:
                self.cleaned_data[field] = self.plan[field]
            self.cleaned_data['Plan_Name'] = self.plan['Lim_Plan_Name']

            beneficiary = ''
            for field in ['Beneficiary_First_Name', 'Beneficiary_Last_Name', 'Beneficiary_Relationship']:
                beneficiary += self.cleaned_data.get(field, '')
            if beneficiary:
                for field in ['Beneficiary_First_Name', 'Beneficiary_Last_Name', 'Beneficiary_Relationship']:
                    if not self.cleaned_data.get(field, ''):
                        self.add_error(
                            field,
                            "{0} is required".format(field.replace('_', ' '))
                        )
            contingent = ''
            for field in ['Contingent_First_Name', 'Contingent_Last_Name', 'Contingent_Relationship']:
                contingent += self.cleaned_data.get(field, '')
            if contingent:
                for field in ['Contingent_First_Name', 'Contingent_Last_Name', 'Contingent_Relationship']:
                    if not self.cleaned_data.get(field, ''):
                        self.add_error(
                            field,
                            "{0} is required".format(field.replace('_', ' '))
                        )
            if not (beneficiary and contingent):
                self.cleaned_data['Estate_Flag'] = '1'
                self.cleaned_data['Estate_Detail'] = 'ESTATE'
            else:
                self.cleaned_data['Estate_Flag'] = '0'
                self.cleaned_data['Estate_Detail'] = ''

            self.cleaned_data['Payment_Agree'] = '1'

        self.cleaned_data['Date_Signed'] = datetime.date.today().strftime("%Y-%m-%d")
        self.cleaned_data['IP_Address'] = (get_ip(self.request) if
                                           self.request.get_host().split(':')[0] == '127.0.0.1'
                                           else get_real_ip(self.request))

        if not self.initial_form_data['applicant_is_child']:
            first_name = self.cleaned_data.get('First_Name', '')
            middle_name = self.cleaned_data.get('Middle_Name', '')
            last_name = self.cleaned_data.get('Last_Name', '')
            self.cleaned_data['Name_Enroll'] = "{0} {2}{1}".format(first_name, last_name,
                                                                   (middle_name + ' ') if middle_name else '')[:75]
            self.cleaned_data['Name_Auth'] = "{0} {2}{1}".format(first_name, last_name,
                                                                   (middle_name + ' ') if middle_name else '')[:75]
        return self.cleaned_data




class STDependentInfoForm(forms.Form):

    def __init__(self, plan=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plan = plan
        print("plan from dependent:", plan)
        self.empty_permitted = False

    Relation = forms.ChoiceField(
        choices=(("Spouse", "Spouse"), ("Child", "Child")),
        label=_("Relation"),
        error_messages={'required': _("Relation is required.")},
        widget=forms.HiddenInput
    )

    First_Name = forms.CharField(
        label=_("First Name"),
        max_length=50,
        error_messages={'required': _("First Name is required.")}
    )

    Middle_Name = forms.CharField(
        required=False,
        max_length=50,
        label=_("Middle Name")
    )

    Last_Name = forms.CharField(
        label=_("Last Name"),
        max_length=50,
        error_messages={'required': _("Last Name is required.")}
    )

    Gender = forms.ChoiceField(
        required=False,
        choices=(
            ("Male", _("Male")),
            ("Female", _("Female"))
        ),
        label=_("Gender"),
        error_messages={'required': _("Gender is required.")}
    )

    DOB = forms.DateField(
        required=False,
        label=_("Date of Birth"),
        error_messages={"required": _("Date of Birth is required.")}
    )

    Age = forms.IntegerField(
        label=_('Age'),
        required=False
    )

    SSN = forms.CharField(
        required=False,
        label=_('Social Security Number'),
    )

    Feet = forms.ChoiceField(
        required=False,
        label=_("Feet"),
        choices=(('2', '2'), ('3', '3'), ('4', '4'),
                 ('5', '5'), ('6', '6'), ('7', '7'))
    )

    Inch = forms.ChoiceField(
        required=False,
        label=_("Inch"),
        choices=(('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'),
                 ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'), ('11', '11'))
    )

    Tobacco = forms.ChoiceField(
        required=False,
        label=_("Tobacco"),
        choices=(
            ("N", "No"),
            ("Y", "Yes"),
        )
    )


    Weight = forms.IntegerField(required=False, label=_("Weight"))

    def clean(self):
        super().clean()
        relation = self.cleaned_data.get('Relation', '')
        if relation == 'Spouse' and self.plan['Name'] not in ['Principle Advantage', 'Cardinal Choice',
                                                              'Vitala Care', 'Health Choice', 'Legion Limited Medical']:
            for field in ['Feet', 'Inch', 'Weight']:
                if not self.cleaned_data.get(field, ''):
                    self.add_error(field, forms.ValidationError("{0} is required".format(field), code='required'))
        return self.cleaned_data


class BaseSTDependentFormSet(BaseFormSet):
    @classmethod
    def get_default_prefix(cls):
        return 'st_dependent'

    def clean(self):
        if any(self.errors):
            return
        for idx, form in enumerate(self.forms):
            form.cleaned_data['DOB'] = QR_DATE_PATTERN.sub(r'\3-\1-\2', self.initial[idx]['DOB'])
            form.cleaned_data['Age'] = self.initial[idx]['Age']
            form.cleaned_data['Gender'] = self.initial[idx]['Gender']
            form.cleaned_data['SSN'] = self.initial[idx]['SSN']
            form.cleaned_data['Tobacco'] = self.initial[idx]['Tobacco']


STDependentInfoFormSet = formset_factory(STDependentInfoForm, formset=BaseSTDependentFormSet, extra=0, max_num=10)


class PaymentMethodForm(forms.Form):

    def __init__(self, applicant_info, initialize_form=None, *args, **kwargs):
        self.applicant_info = applicant_info
        self.initialize_form = initialize_form
        if self.initialize_form:
            super().__init__(initial={"Billing_Address": self.applicant_info["Address"],
                                      'Billing_City': self.applicant_info["City"],
                                      "Billing_State": self.applicant_info["State"],
                                      "Billing_ZipCode": self.applicant_info["ZipCode"]}, *args, **kwargs)
        else:
            super().__init__(*args, **kwargs)
        #print(self.initial)

    Payment_Method = forms.ChoiceField(
        choices=(("CreditCard", "Credit Card"),
                 ("BankDraft", "Bank Draft")),
        error_messages={"required": "Payment Method is required.",
                        "invalid_choice": "Invalid Payment method."}
    )

    # required for payment method - CreditCard
    Card_Type = forms.ChoiceField(
        choices=(("VISA", "Visa Card"), ("MasterCard", "Master Card")),
        required=False,
        error_messages={"invalid_choice": "%(value)s is not a valid Card Type."}
    )

    Card_Number = forms.CharField(required=False)

    Card_ExpirationMonth = forms.ChoiceField(
        choices=(('01', '01'), ('02', '02'), ('03', '03'), ('04', '04'),
                 ('05', '05'), ('06', '06'), ('07', '07'), ('08', '08'),
                 ('09', '09'), ('10', '10'), ('11', '11'), ('12', '12')),
        required=False,
        error_messages={"invalid_choice": "%(value)s is not a valid Card Expiration Month."}
    )

    Card_ExpirationYear = forms.ChoiceField(
        choices=get_years_for_card,
        required=False
    )

    CardHolder_Name = forms.CharField(required=False, max_length=75)

    # required for payment method - BankDraft
    Bank_Account_Name = forms.CharField(required=False, max_length=75)

    Bank_Account_Class = forms.ChoiceField(
        choices=(("Checking", "Checking"), ("Saving", "Saving")),
        required=False
    )

    Bank_Account_Type = forms.ChoiceField(
        choices=(("Personal", "Personal"), ("Business", "Business")),
        required=False
    )

    Bank_Name = forms.CharField(required=False, max_length=100)

    Bank_Routing_Number = forms.CharField(required=False)

    Bank_Account_Number = forms.CharField(required=False)

    Bank_Check_Number = forms.CharField(required=False)

    # both for card & bank
    Payment_Agree = forms.BooleanField(
        error_messages={"required": _("You must agree with payment terms & conditions.")}
    )

    # Billing Address Info
    same_as_contact_address = forms.BooleanField(required=False, initial=False)

    Billing_Address = forms.CharField(required=False)

    Billing_City = forms.CharField(required=False)

    Billing_State = forms.ChoiceField(choices=states, required=False)

    Billing_ZipCode = forms.IntegerField(required=False)

    def _card_clean_card_number(self):
        card_number = self.cleaned_data.get('Card_Number', '')
        if not card_number:
            self.add_error('Card_Number', forms.ValidationError(_("Card Number is required."), code='required'))
            return ''
        card = Card(card_number)
        if not card.is_valid or (settings.TEST_CARD_ALLOWED is False and card.is_test):
            if card.brand == card.BRAND_UNKNOWN and card.is_mod10_valid:
                self.add_error(
                    'Card_Number',
                    forms.ValidationError(_("Only Visa and MasterCard is accepted."), code='invalid')
                )
                return ''
            self.add_error(
                'Card_Number',
                forms.ValidationError(_("Invalid Card Number."), code='invalid')
            )
            return ''
        self.cleaned_data['Card_Number'] = card.number
        self.cleaned_data['Card_Type'] = card.friendly_brand
        return card.number

    def _card_clean_card_expiration(self):
        month = self.cleaned_data.get('Card_ExpirationMonth', '')
        if not month:
            self.add_error('Card_ExpirationMonth',
                           forms.ValidationError(_("Card Expiration Month is required."), code='required'))
        year = self.cleaned_data.get('Card_ExpirationYear', '')
        if not year:
            self.add_error('Card_ExpirationYear',
                           forms.ValidationError(_("Card Expiration Year is required"), code='required'))
        if not month or not year:
            return ''
        exp_date = ExpDate(int(month), int(year))
        if exp_date.is_expired:
            self.add_error('Card_ExpirationMonth', forms.ValidationError(_("Card Expired"), code='invalid'))
            return ''
        self.cleaned_data['Card_ExpirationMonth'] = exp_date.mm
        self.cleaned_data['Card_ExpirationYear'] = exp_date.yyyy
        return exp_date.mmyyyy

    def _card_clean_card_holder_name(self):
        name = self.cleaned_data.get('CardHolder_Name', '')
        if not name:
            self.add_error('CardHolder_Name',
                           forms.ValidationError(_("Card Holder Name is required."), code='required'))
            return ''
        self.cleaned_data['CardHolder_Name'] = name
        return name

    def _remove_card_fields_error(self):
        for field in ['Card_Type', 'Card_Number', 'Card_ExpirationMonth',
                      'Card_ExpirationYear', 'CardHolder_Name']:
            if self.has_error(field):
                del self._errors[field]

    def _clean_bank_routing_number(self):
        rtn_number = self.cleaned_data.get('Bank_Routing_Number', '')
        if not rtn_number:
            return ''
        if not is_valid_rtn(rtn_number):
            self.add_error('Bank_Routing_Number',
                           forms.ValidationError(_("Invalid Bank Routing Number"), code='invalid'))
            return ''
        self.cleaned_data['Bank_Routing_Number'] = clean_number(rtn_number)
        return clean_number(rtn_number)

    def _clean_bank_account_number(self):
        account_number = self.cleaned_data.get('Bank_Account_Number', '')
        if not account_number:
            return ''
        account_number = clean_number(account_number)
        if not (4 < len(account_number) < 30):
            self.add_error('Bank_Account_Number',
                           forms.ValidationError(_("Invalid Bank Account Number"), code='invalid'))
            return ''
        self.cleaned_data['Bank_Account_Number'] = account_number
        return account_number

    def _clean_bank_check_number(self):
        check_number = self.cleaned_data.get('Bank_Check_Number', '')
        if not check_number:
            return ''
        check_number = clean_number(check_number)
        if not (2 < len(check_number) <= 5):
            self.add_error('Bank_Check_Number',
                           forms.ValidationError(_("Invalid Bank Check Number"), code='invalid'))
            return ''
        self.cleaned_data['Bank_Check_Number'] = check_number
        return check_number

    def _clean_bank_required(self):
        for field in ['Bank_Account_Name', 'Bank_Account_Class', 'Bank_Account_Type', 'Bank_Name',
                      'Bank_Routing_Number', 'Bank_Account_Number', 'Bank_Check_Number']:
            if not self.cleaned_data.get(field, ''):
                self.add_error(
                    field,
                    forms.ValidationError("{0} is required.".format(field.replace('_', ' ')), code='required')
                )
        self._clean_bank_routing_number()
        self._clean_bank_account_number()
        self._clean_bank_check_number()

    def _remove_bank_fields_error(self):
        for field in ['Bank_Account_Name', 'Bank_Account_Class', 'Bank_Account_Type', 'Bank_Name',
                      'Bank_Routing_Number', 'Bank_Account_Number', 'Bank_Check_Number']:
            if self.has_error(field):
                del self._errors[field]

    def _clean_billing_required(self):
        for field in ['Billing_Address', 'Billing_City', 'Billing_State', 'Billing_ZipCode']:
            if not self.cleaned_data.get(field, ''):
                self.add_error(
                    field,
                    forms.ValidationError("{0} is required.".format(field.replace('_', ' ')), code='required')
                )

    def _clean_billing_fields(self):
        for field in ['Billing_Address', 'Billing_City', 'Billing_State', 'Billing_ZipCode']:
            self.cleaned_data[field] = self.applicant_info.get(field.replace('Billing_', ''), '')
            if not self.cleaned_data[field]:
                self.add_error(
                    field,
                    forms.ValidationError("Please Complete the Applicant Info Step Carefully.", code='required')
                )

    def clean(self):
        super().clean()
        payment_method = self.cleaned_data.get('Payment_Method', '')
        same_as_contact_address = self.cleaned_data.get('same_as_contact_address', False)
        if payment_method == 'CreditCard':
            self._remove_bank_fields_error()
            self._card_clean_card_number()
            self._card_clean_card_expiration()
            self._card_clean_card_holder_name()
        elif payment_method == 'BankDraft':
            self._remove_card_fields_error()
            self._clean_bank_required()
        if same_as_contact_address:
            self._clean_billing_fields()
        else:
            self._clean_billing_required()
        return self.cleaned_data


class GetEnrolledForm(forms.Form):

    consent = forms.BooleanField()


class LeadForm(forms.ModelForm):

    Applicant_DOB = forms.DateField(
        input_formats=[
            '%Y-%m-%d',      # '2006-10-25'
            '%m/%d/%Y',      # '10/25/2006'
            '%m/%d/%y',      # '10/25/06'
            '%m-%d-%Y',      # '04-27-2004'
        ]
    )

    Applicant_Gender = forms.ChoiceField(
        label=_("Applicant Gender"),
        choices=(
            ("Male", _("Male")),
            ("Female", _("Female"))
        ),
        error_messages={"required": _("Applicant Gender is required.")},
        required=True
    )

    Zip_Code = forms.CharField(
        label=_("Zip Code"),
        max_length=5,
        min_length=5,
        strip=True,
        error_messages={'required': _("Zip Code is required.")}
    )

    quote_store_key = forms.CharField(
        max_length=500,
    )



    # def clean_Phone(self):
    #     phone = self.cleaned_data.get('Phone', '')
    #     return clean_number(phone)

    class Meta:
        model = Leads
        exclude = ['created']


class AddonPlanForm(forms.Form):

    def __init__(self, addon_plans, selected_addon_plans, *args, **kwargs):
        self.addon_plans = addon_plans
        self.selected_addon_plans = selected_addon_plans
        self.addon_plan = None
        self._add_on_with_same_id = None
        self._add_on_with_same_carrier_id = None
        super().__init__(*args, **kwargs)

    stm_name = forms.ChoiceField(
        choices=(
            ('Everest STM', 'Everest STM'),
            ('LifeShield STM', 'LifeShield STM'),
            ('HealtheFlex STM', 'HealtheFlex STM'),
            ('AdvantHealth STM', 'AdvantHealth STM'),
            ('HealtheFlex STM', 'HealtheFlex STM'),
            ('HealtheMed STM', 'HealtheMed STM'),
            ('Premier STM', 'Premier STM'),
            ('Sage STM', 'Sage STM'),
            ('Unified Health One', 'Unified Health One'),
            ('Principle Advantage', 'Principle Advantage'),
            ('Select STM', 'Select STM'),
            ('Cardinal Choice', 'Cardinal Choice'),
            ('Vitala Care', 'Vitala Care'),
            ('Health Choice', 'Health Choice'),
            ('Legion Limited Medical', 'Legion Limited Medical')
        )
    )

    addon_id = forms.IntegerField()

    Name = forms.CharField()

    Premium = forms.CharField()

    AdministrativeFee = forms.CharField()

    EnrollmentFee = forms.CharField()

    MedsenseFee = forms.CharField()

    Embeded = forms.CharField()

    Plan = forms.CharField(required=False)

    Plan_Code = forms.CharField(required=False)

    Deductible = forms.CharField(required=False)

    def is_add_on_with_same_id_exist(self, add_on_id):
        try:
            self._add_on_with_same_id = next(filter(
                lambda add_on: str(add_on.addon_id) == str(add_on_id),
                self.selected_addon_plans
            ))
        except StopIteration:
            return False
        return True

    def is_add_on_with_same_carrier_id(self, carrier_id):
        try:
            self._add_on_with_same_carrier_id = next(filter(
                lambda add_on: str(add_on.carrier_id) == str(carrier_id),
                self.selected_addon_plans
            ))
        except StopIteration:
            return False
        return True

    def add_addon_plan(self):
        if not self.cleaned_data:
            return False
        self.addon_plan = AddonPlan(**self.cleaned_data)
        if self.addon_plan not in self.addon_plans:
            self.add_error(
                None,
                forms.ValidationError(
                    "Invalid addon plan. Addon plan does not exists.",
                    code='invalid'
                )
            )
            return False
        if self.addon_plan in self.selected_addon_plans:
            self.add_error(
                None,
                forms.ValidationError(
                    "Add-on plan has already been selected.",
                    code='invalid'
                )
            )
            return False
        if self.is_add_on_with_same_id_exist(self.addon_plan.addon_id):
            self.add_error(
                None,
                forms.ValidationError(
                    "Can't choose more than one plan from {0}".format(self._add_on_with_same_id.carrier_name),
                    code='invalid'
                )
            )
            return False
        if self.is_add_on_with_same_carrier_id(self.addon_plan.carrier_id):
            self.add_error(
                None,
                forms.ValidationError(
                    "Can't choose '{0}' and '{1}' together".format(self._add_on_with_same_carrier_id.carrier_name,
                                                                   self.addon_plan.carrier_name),
                    code='invalid'
                )
            )
            return False
        return True

    def remove_addon_plan(self):
        if not self.cleaned_data:
            return False
        self.addon_plan = AddonPlan(**self.cleaned_data)
        if self.addon_plan not in self.addon_plans:
            self.add_error(
                None,
                forms.ValidationError(
                    "Invalid addon plan. Addon plan does not exists.",
                    code='invalid'
                )
            )
            return False
        if self.addon_plan not in self.selected_addon_plans:
            self.add_error(
                None,
                forms.ValidationError(
                    "The addon plan is not in your selected addon plan list.",
                    code='invalid'
                )
            )
            return False
        return True
