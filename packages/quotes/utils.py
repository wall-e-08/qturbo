from __future__ import unicode_literals, print_function

import os
import re
import copy
import time
import string
import random
import hashlib
import datetime
from typing import Union

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from .logger import VimmLogger
# from quotes.tasks import send_mail_task


logger = VimmLogger('quote_turbo')

QR_DATE_PATTERN = re.compile(r'^(\d{2})-(\d{2})-(\d{4})$')


def age(dob):
    today = datetime.date.today()
    if today.month < dob.month or (today.month == dob.month and today.day < dob.day):
        return today.year - dob.year - 1
    return today.year - dob.year


def get_img_path(instance, filename):
    file_extension = os.path.splitext(filename)[1]
    return os.path.join(
        "benefits",
        str("{}-{}".format(instance.title, ''.join(random.choices(string.ascii_letters + string.digits, k=8))) + file_extension)
    )

# def date_from_str(date_str, date_format='%d-%M-%Y'):
#     if not isinstance(date_str, str):
#         return date_str
#     return datetime.datetime.strptime(date_str, date_format)


def form_data_is_valid(form_data):
    effective_date = form_data.get('Effective_Date', None)
    if effective_date is None:
        return False
    effective_date = datetime.datetime.strptime(effective_date, '%m-%d-%Y').date()
    return effective_date > datetime.date.today()


def get_app_stage(stage, stm_stages):
    if stage > 1 and stage - 1 not in stm_stages:
        return get_app_stage(stage - 1, stm_stages)
    return stage


def get_initials_for_dependents_formset(initial_form_data):
    initial = []
    if initial_form_data['Include_Spouse'] == 'Yes':
        initial.append(
            {"Relation": "Spouse", "Gender": initial_form_data["Spouse_Gender"],
             "DOB": QR_DATE_PATTERN.sub(r'\3-\1-\2', initial_form_data["Spouse_DOB"]),
             "Age": initial_form_data["Spouse_Age"],
             "Tobacco": initial_form_data["Spouse_Tobacco"]}
        )
    if initial_form_data["Dependents"]:
        for dependent in initial_form_data["Dependents"]:
            initial.append({"Relation": "Child", "Gender": dependent["Child_Gender"],
                            "DOB": QR_DATE_PATTERN.sub(r'\3-\1-\2', dependent["Child_DOB"]),
                            "Age": dependent["Child_Age"], "Tobacco": dependent["Child_Tobacco"]})
    return initial


def get_st_dependent_info_formset(formset_class, initial_form_data):
    initial = get_initials_for_dependents_formset(initial_form_data)
    if initial:
        return formset_class(initial=initial)
    return formset_class()


def clean_number(number):
    _numbers = []
    for n in str(number):
        try:
            _numbers.append(str(int(n)))
        except ValueError:
            pass
    return "".join(_numbers)


def get_years_for_card():
    current_year = datetime.datetime.now().year
    return [(str(year), str(year)) for year in range(current_year, current_year + 20)]


try:
    random = random.SystemRandom()
    using_sysrandom = True
except NotImplementedError:
    import warnings
    warnings.warn('A secure pseudo-random number generator is not available '
                  'on your system. Falling back to Mersenne Twister.')
    using_sysrandom = False


def get_random_string(length=12,
                      allowed_chars='abcdefghijklmnopqrstuvwxyz'
                                    'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    if not using_sysrandom:
        random.seed(
            hashlib.sha256(
                ("%s%s%s" % (
                    random.getstate(), time.time(),
                    settings.SECRET_KEY)).encode('utf-8')
            ).digest())
    return ''.join(random.choice(allowed_chars) for i in range(length))


def save_lead_info(stm_lead_model, lead_form_cleaned_data):
    """ We are saving  quote store key without the last parts ie: stm, lim, anc

    :param stm_lead_model:
    :param lead_form_cleaned_data:
    :return:
    """

    try:
        stm_lead_obj = stm_lead_model(
            Zip_Code=lead_form_cleaned_data['Zip_Code'],
            DOB=lead_form_cleaned_data['Applicant_DOB'],
            Gender=lead_form_cleaned_data['Applicant_Gender'],
            quote_store_key=lead_form_cleaned_data['quote_store_key'][:-4]
        )
        print(f'Saving lead form info')
        stm_lead_obj.save()
        return stm_lead_obj
    except KeyError:
        logger.warning("Unable to save lead data")


def update_lead_vimm_enroll_id(stm_lead_model, quote_store_key, vimm_enroll_id):
    try:
        stm_lead_obj = stm_lead_model.objects.filter(quote_store_key=quote_store_key[:-4]).latest('created')
        stm_lead_obj.vimm_enroll_id = vimm_enroll_id
        stm_lead_obj.save()
        return stm_lead_obj
    except Exception as e:
        print(f'Cannot update lead info Vimm enrollment ID. The following exception happened:\n'
        f'{e}')


def update_leads_stm_id(stm_lead_model, stm_enroll_obj, quote_store_key):
    """
    :return:
    """
    try:
        stm_lead_obj = stm_lead_model.objects.filter(
            quote_store_key=quote_store_key[:-4],
            vimm_enroll_id=stm_enroll_obj.vimm_enroll_id
        ).latest('created')
        stm_lead_obj.stm_enroll = stm_enroll_obj
        stm_lead_obj.save()
        return stm_lead_obj
    except Exception as e:
        print(f'Cannot update lead info stm enrollment ID. The following exception happened:\n'
              f'{e}')



def update_applicant_info(stm_enroll_obj, applicant_info, applicant_parent_info, plan):
    """I am recreating update_applicant_info method such that it does not need session vars.

    :param stm_enroll_obj:
    :param request:
    :param plan:
    :return:
    """

    for field in ['First_Name', 'Middle_Name', 'Last_Name', 'Gender', 'DOB', 'Applicant_is_Child',
                  'Age', 'Feet', 'Inch', 'IP_Address', 'Weight', 'Address', 'City', 'State',
                  'ZipCode', 'Email', 'DayPhone', 'CellPhone', 'Mailing_Name', 'Mailing_Address',
                  'Mailing_City', 'Mailing_State', 'Mailing_ZipCode']:
        if (field in ['Feet', 'Inch', 'Weight']) and (plan['Name'] in [
                'Principle Advantage', 'Cardinal Choice', 'Vitala Care',
                'Health Choice', 'Legion Limited Medical', 'Foundation Dental',
                'USA Dental', 'Safeguard Critical Illness', 'Freedom Spirit Plus']):
            continue
        setattr(stm_enroll_obj, field, applicant_info[field])
    if applicant_parent_info:
        for field in ['Name_Enroll', 'Name_Auth', 'Parent_First_Name', 'Parent_Middle_Name', 'Parent_Last_Name',
                      'Parent_Gender', 'Parent_DOB', 'Parent_Address', 'Parent_City', 'Parent_State',
                      'Parent_ZipCode', 'Parent_Email', 'Parent_DayPhone', 'Parent_CellPhone']:
            setattr(stm_enroll_obj, field, applicant_parent_info.get(field, ''))
    else:
        stm_enroll_obj.Name_Enroll = applicant_info['Name_Enroll']
        stm_enroll_obj.Name_Auth = applicant_info['Name_Auth']
    stm_enroll_obj.save()

    return stm_enroll_obj


def save_applicant_info(stm_enroll_model, applicant_info, applicant_parent_info, plan, plan_url):
    """I am recreating save_applicant_info method such that it does not need session vars.

    :param stm_enroll_model:
    :param applicant_info:
    :param applicant_parent_info:
    :param plan:
    :param plan_url:
    :return:
    """
    stm_enroll_obj = stm_enroll_model(vimm_enroll_id=plan['vimm_enroll_id'], stm_name=plan['Name'])
    for field in ['First_Name', 'Middle_Name', 'Last_Name', 'Gender', 'DOB', 'Applicant_is_Child', 'Tobacco',
                  'Age', 'Feet', 'Inch', 'IP_Address', 'Effective_Date', 'Weight', 'Address', 'City',
                  'State', 'ZipCode', 'Email', 'DayPhone', 'CellPhone', 'Mailing_Name', 'Mailing_Address',
                  'Mailing_City', 'Mailing_State', 'Mailing_ZipCode']:
        if (field in ['Feet', 'Inch', 'Weight']) and (plan['Name'] in [
                'Principle Advantage', 'Cardinal Choice', 'Vitala Care',
                'Health Choice', 'Legion Limited Medical', 'Foundation Dental',
                'USA Dental', 'Safeguard Critical Illness', 'Freedom Spirit Plus']):
            print("{0} is not needed in {1}".format(field, plan['Name']))
            continue
        setattr(stm_enroll_obj, field, applicant_info[field])
    if applicant_parent_info:
        for field in ['Name_Enroll', 'Name_Auth', 'Parent_First_Name', 'Parent_Middle_Name', 'Parent_Last_Name',
                      'Parent_Gender', 'Parent_DOB', 'Parent_Address', 'Parent_City', 'Parent_State',
                      'Parent_ZipCode', 'Parent_Email', 'Parent_DayPhone', 'Parent_CellPhone']:
            setattr(stm_enroll_obj, field, applicant_parent_info.get(field, ''))
    else:
        stm_enroll_obj.Name_Enroll = applicant_info['Name_Enroll']
        stm_enroll_obj.Name_Auth = applicant_info['Name_Auth']

    setattr(stm_enroll_obj, 'app_url', plan_url)
    stm_enroll_obj.save()


    return stm_enroll_obj

def save_applicant_payment_info(stm_enroll_obj, request, plan_url):
    payment_info = request.session.get('payment_info_{0}'.format(plan_url), {})

    # We should not save Payment information in database
    for field in [
        # 'Bank_Account_Name',
        # 'Bank_Account_Number',
        # 'Bank_Account_Type',

        # 'Bank_Check_Number',
        # 'Bank_Name',
        # 'Bank_Routing_Number',
        'Payment_Method',
        'Payment_Agree',

        'same_as_contact_address'
    ]:
        setattr(stm_enroll_obj, field, payment_info[field])
    stm_enroll_obj.save()

    return stm_enroll_obj


def save_dependent_info(dependent_model, dependents_info_form_data, plan, stm_enroll_obj):
    dependents = []
    for dependent_info in copy.deepcopy(dependents_info_form_data):
        for field in ['Feet', 'Inch', 'Weight']:
            dependent_info[field] = dependent_info[field] or None
        if plan['Name'] in ['Principle Advantage']:
            for field in ['Feet', 'Inch', 'Weight']:
                dependent_info[field] = None

        dependents.append(dependent_model.objects.create(
            stm_enroll=stm_enroll_obj,
            vimm_enroll_id=plan['vimm_enroll_id'],
            **dependent_info
        ))
    return dependents


def update_dependent_info(dependents_info_obj, dependent_info_form_data):
    for dependent_info, dependent_obj in zip(copy.deepcopy(dependent_info_form_data), dependents_info_obj):
        if str(dependent_obj.DOB) == dependent_info['DOB']:
            for field in ['Feet', 'Inch', 'Weight']:
                dependent_info[field] = dependent_info[field] or None
            for field in ['Relation', 'First_Name', 'Middle_Name',
                          'Last_Name', 'Gender', 'DOB', 'Age',
                          'Feet', 'Inch', 'Weight', 'SSN']:
                setattr(dependent_obj, field, dependent_info[field])

            dependent_obj.save()
        else:
            logger.warning("Date of birth does not match for dependent {0} {1}".format(dependent_info['First_Name'],
                                                                                       dependent_info['Last_Name']))

    return dependents_info_obj

#
def save_add_on_info(add_on_model, selected_add_on_plans, plan, stm_enroll_obj):
    add_ons = []
    for add_on_plan in selected_add_on_plans:
        add_ons.append(add_on_model.objects.create(
            stm_enroll=stm_enroll_obj,
            vimm_enroll_id=plan['vimm_enroll_id'],
            **add_on_plan
        ))
    return add_ons


def get_plan_type_principle_limited(form_data):
    if ((form_data['Include_Spouse'] == 'Yes' and len(form_data['Dependents']) == 0) or
            (form_data['Include_Spouse'] == 'No' and len(form_data['Dependents']) == 1)):
        return 'Member+1'
    if ((form_data['Include_Spouse'] == 'Yes' and len(form_data['Dependents']) >= 1) or
            (form_data['Include_Spouse'] == 'No' and len(form_data['Dependents']) > 1)):
        return 'Family'
    return 'Single Member'


def save_stm_plan(qm, plan, stm_enroll_obj):
    # if plan['Name'] == 'Principle Advantage':
    #     plan['Plan_Type'] = get_plan_type_principle_limited(copy.deepcopy(quote_request_form_data))

    stm_plan_model = getattr(qm, 'MainPlan')
    stm_plan_obj = stm_plan_model(stm_enroll=stm_enroll_obj, **plan)
    stm_plan_obj.save()
    return stm_plan_obj


def update_addon_plan_at_enroll(stm_enroll_obj, add_ons):
    fields = ['Member_ID']
    for add_on in add_ons:
        try:
            add_on_obj = stm_enroll_obj.addonplan_set.get(addon_id=add_on['ID'], carrier_name=add_on['Name'])
            add_on_obj.Member_ID = add_on.get('Member_ID', None)
            add_on_obj.save(update_fields=fields)
        except ObjectDoesNotExist as err:
            print(err)
    return stm_enroll_obj


def save_enrolled_applicant_info(stm_enroll_obj, enrolled_applicant_info, enrolled=True):
    fields = ['Member_ID', 'Payment_Status_Date', 'Password', 'User_ID',
              'Status', 'ApplicantID', 'LoginURL', 'enrolled']

    for field in fields:
        if field in ['Payment_Status_Date']:
            setattr(stm_enroll_obj, field, QR_DATE_PATTERN.sub(r'\3-\1-\2', enrolled_applicant_info.get(field, '')))
            continue
        setattr(stm_enroll_obj, field, enrolled_applicant_info.get(field, None))

    stm_enroll_obj.enrolled = True
    stm_enroll_obj.save(update_fields=fields)

    if stm_enroll_obj.addonplan_set.count() and enrolled_applicant_info.get('Add_ons', None):
        update_addon_plan_at_enroll(stm_enroll_obj, enrolled_applicant_info.get('Add_ons', []))
    return stm_enroll_obj
#

def get_askable_questions(sorted_question):
    quss = []
    for qus in sorted_question:
        if qus.get('SubQue', None) is None:
            quss.append(qus)
        else:
            for sub_qus in qus['SubQue']:
                quss.append(sub_qus)
    return quss


def get_quote_store_key(form_data):
    """

    :param form_data: Quotation request form data.
    :type form_data: python dictionary object
    :return: str: Nearly unique key which is then
    concatanated with session key to form redis key.
    """
    _key = '{0}-{1}-{2}-{3}-{4}-{5}'.format(form_data['Zip_Code'], form_data['Applicant_DOB'],
                                            form_data['Applicant_Gender'], form_data['Payment_Option'],
                                            form_data['Effective_Date'], form_data['Tobacco'])
    if form_data['Coverage_Days']:
        _key += '-{0}'.format(form_data['Coverage_Days'])
    if form_data['Include_Spouse'] == 'Yes':
        _key += '-{0}-{1}'.format(form_data['Spouse_DOB'], form_data['Spouse_Gender'])
    if form_data['Dependents']:
        for dependent in form_data['Dependents']:
            _key += '-{0}-{1}'.format(dependent['Child_DOB'], dependent['Child_Gender'])

    _key += '-{0}'.format(form_data['Ins_Type'])
    return _key

#
# def send_enroll_email(request, form_data, enroll,
#                       stm_enroll_obj,
#                       subject_template_name='quotes/mail/enroll_mail_subject.html',
#                       email_template_name='quotes/mail/enrollment_mail.html',
#                       html_email_template_name='quotes/mail/enrollment_mail.html',
#                       extra_email_context=None, from_email=None):
#     context = {
#         'enroll': enroll,
#         'domain': request.site.domain,
#         'site_name': request.site.name,
#         'protocol': request.site.protocol
#     }
#     if extra_email_context is not None:
#         context.update(extra_email_context)
#     logger.info("Sending enroll mail to {0}".format(form_data['Email']))
#     send_mail_task.apply_async(
#         [subject_template_name, email_template_name, context,
#          from_email, stm_enroll_obj.Email, html_email_template_name]
#     )
#
#
# def send_sales_notification(
#         request,
#         stm_enroll_obj,
#         subject_template_name='quotes/mail/enroll_notification_email_subject.html',
#         email_template_name='quotes/mail/enroll_notification_email.html',
#         html_email_template_name='quotes/mail/enroll_notification_email.html',
#         extra_email_context=None,
#         from_email=None,
#         to_email=settings.SALES_ADMIN):
#     context = {
#         'stm_enroll_obj': stm_enroll_obj,
#         'domain': request.site.domain,
#         'site_name': request.site.name,
#         'protocol': request.site.protocol
#     }
#     if extra_email_context is not None:
#         context.update(extra_email_context)
#     send_mail_task.apply_async(
#         [subject_template_name, email_template_name, context,
#          from_email, to_email, html_email_template_name]
#     )
#

def validate_name(name, allowed_chars="abcdefghijklmnopqrstuvwxyz"
                                      "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 '_-."):
    for char in name:
        if char not in allowed_chars:
            return False
    return True

def update_application_stage(stm_enroll_obj, stage):
    if (stm_enroll_obj.stage < stage) and (stage <= 5):
        stm_enroll_obj.stage = stage
        stm_enroll_obj.save(update_fields=['stage'])
    return stm_enroll_obj
#
def log_user_info(dict):
    info = {
        'User Name': dict.get('Name_Enroll', ''),
        'User Email': dict.get('Email', '')
    }
    return info


#
DURATION_RE = re.compile(r'(?P<duration>\d{1,2})\*(?P<times>\d{1})')


def parse_stm_duration(stm_duration):
    """
    Is used in templates.

    :param stm_duration: stm duration in (month * times) format
    :type stm_duration: str
    :return: stm duration in int format
    """

    match = DURATION_RE.match(stm_duration)
    if not match and stm_duration in string.digits:
        return int(stm_duration)
    return int(match.groupdict()['duration']) * int(match.groupdict()['times'])


def create_selection_data(completed_data: dict, stm_name: str, duration_coverage: str) -> Union [dict, None]:
    """ Create intermidiate quote request selection data from
    completed data and preferred coverage duration.

    :return: dict
    """
    quote_request_data : dict = {
        'LifeShield STM': {
            'Duration_Coverage': [],
        },

        'AdvantHealth STM': {
            'Duration_Coverage': []
        }
    }

    if duration_coverage not in completed_data[stm_name]['Duration_Coverage']:
        quote_request_data[stm_name]['Duration_Coverage'] = [duration_coverage]
        return quote_request_data
    else:
        return None


def get_dict_for_available_alternate_plans(plan_list: list, selected_plan) -> dict:
    # plan_list = plan_list.remove(selected_plan)

    coins_set = set()
    out_of_pocket_set = set()
    coverage_max_set = set()
    plan_set = set()


    print("Finding out alternative coinsurance.")
    for plan in plan_list:

        if (plan["out_of_pocket_value"] == selected_plan['out_of_pocket_value'] and
            plan['Duration_Coverage'] == selected_plan['Duration_Coverage'] and
            plan['Coverage_Max'] == selected_plan['Coverage_Max'] and
            plan["Name"] == selected_plan["Name"] and
            plan['Plan'] == selected_plan['Plan'] and
            plan != selected_plan):

                coins_set.add(plan['Coinsurance_Percentage'])

    print("Finding out alternative max_out_of_pocket.")
    for plan in plan_list:

        if (plan["Coinsurance_Percentage"] == selected_plan['Coinsurance_Percentage'] and
            plan['Duration_Coverage'] == selected_plan['Duration_Coverage'] and
            plan['Coverage_Max'] == selected_plan['Coverage_Max'] and
            plan["Name"] == selected_plan["Name"] and
            plan['Plan'] == selected_plan['Plan'] and
            plan != selected_plan):

                out_of_pocket_set.add(plan['Benefit_Amount'])



    print("Finding out alternative maximum coverage.")

    for plan in plan_list:

        if (plan["out_of_pocket_value"] == selected_plan['out_of_pocket_value'] and
            plan['Duration_Coverage'] == selected_plan['Duration_Coverage'] and
            plan['Coinsurance_Percentage'] == selected_plan['Coinsurance_Percentage'] and
            plan["Name"] == selected_plan["Name"] and
            plan['Plan'] == selected_plan['Plan'] and
            plan != selected_plan):
                coverage_max_set.add(plan['Coverage_Max'])

    print("Finding out alternative plan type.")

    for plan in plan_list:

        if (plan["out_of_pocket_value"] == selected_plan['out_of_pocket_value'] and
                plan['Duration_Coverage'] == selected_plan['Duration_Coverage'] and
                plan['Coinsurance_Percentage'] == selected_plan['Coinsurance_Percentage'] and
                plan["Name"] == selected_plan["Name"] and
                plan['Coverage_Max'] == selected_plan['Coverage_Max'] and
                plan != selected_plan):
            plan_set.add(plan['Plan'])

    return {
        'alternate_benefit_amount': out_of_pocket_set,
        'alternate_coinsurace_percentage': coins_set,
        'alternate_coverage_max': coverage_max_set,
        'alternate_plan': plan_set,
    }


def get_available_coins_against_benefit(plan_list: list, benefit_amount: str, selected_plan: dict) -> dict:

    coins_set = set()


    print(f"Finding out alternative coinsurance for {benefit_amount}.")
    for plan in plan_list:

        if (plan["out_of_pocket_value"] == benefit_amount and
            plan['Duration_Coverage'] == selected_plan['Duration_Coverage'] and
            plan['Coverage_Max'] == selected_plan['Coverage_Max'] and
            plan["Name"] == selected_plan["Name"] and
            plan['Plan'] == selected_plan['Plan'] and
            plan != selected_plan):

                coins_set.add(plan['Coinsurance_Percentage'])

    return list(coins_set)


def get_available_benefit_against_coins(plan_list: list, coinsurance: str, selected_plan: dict) -> dict:

    out_of_pocket_set = set()


    print(f"Finding out alternative benefit amount for {coinsurance}.")
    for plan in plan_list:

        if (plan["Coinsurance_Percentage"] == coinsurance and
            plan['Duration_Coverage'] == selected_plan['Duration_Coverage'] and
            plan['Coverage_Max'] == selected_plan['Coverage_Max'] and
            plan["Name"] == selected_plan["Name"] and
            plan['Plan'] == selected_plan['Plan'] and
            plan != selected_plan):


                out_of_pocket_set.add(plan['Benefit_Amount'])

    return list(out_of_pocket_set)
