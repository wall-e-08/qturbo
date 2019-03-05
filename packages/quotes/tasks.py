from __future__ import absolute_import, unicode_literals

import re
import os
import copy
# import time
import json
import uuid

import redis
import requests

from datetime import timedelta

from geoip2 import database as geo_database

from celery import shared_task
from celery.task import PeriodicTask, Task
from celery.utils.log import get_task_logger

# from quotes.mail import send_mail
from quotes.models import Carrier
from quotes.quote_thread import threaded_request, new_addon_plan_to_add, addon_plans_from_json_data, \
    addon_plans_from_dict
from quotes.quote_request import PROVIDERS
# from quotes.models import StmEnroll
from quotes.logger import VimmLogger

# from quotes.enroll import ESignResponse, ESignVerificationEnroll, Response as EnrollResponse

from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist


QR_DATE_PATTERN = re.compile(r'^(\d{2})-(\d{2})-(\d{4})$')

json_encoder = json.JSONEncoder()
json_decoder = json.JSONDecoder()


# reader = geo_database.Reader('geoip/GeoLite2-City.mmdb')

REDIS_CLIENT = redis.Redis.from_url(
    url=os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
)

# Two separate tasks might not be necessary.
@shared_task
def get_stm_plan_task(session_key, form_data):
    """
    :param session_key: str: key when a session is created
    :param form_data: quote request form data from plan.html
    :return: zero
    """
    threaded_request(copy.deepcopy(form_data), session_key)
    return 0


@shared_task
def get_lim_plan_task(session_key, form_data):
    threaded_request(copy.deepcopy(form_data), session_key)
    return 0

#
# @shared_task
# def send_mail_task(subject_template_name, email_template_name,
#                    context, from_email, to_email, html_email_template_name=None):
#     send_mail(subject_template_name, email_template_name,
#               context, from_email, to_email,
#               html_email_template_name=html_email_template_name)
#     return 0


# @shared_task
# def send_form_data_to_remoteurl(form_data, ipAddress):
#     """
#     function for sending applicant info form data to a remote url
#
#     """
#     print("send_form_data_to_remoteurl: Form DATA LOADING\n\n")
#
#     respon = reader.city(ipAddress)
#
#     form_specific_data = {'FirstName': form_data['First_Name'], 'LastName': form_data['Last_Name'], 'Email': form_data['Email'],
#                           'Phone': form_data['Phone'].replace('-', ''), 'Zip': form_data['Zip_Code'], 'City': respon.city.name,
#                           'State': form_data['State'], 'CampaignId': '01625F85AC735D13212B6654986F57A0', 'Address1': form_data['Address1']}
#
#     print("send_form_data_to_remoteurl: {0}".format(form_specific_data))
#     try:
#         r = requests.post("https://leads.callblade.com/Leads/LeadPost.aspx", data=form_specific_data, timeout=(10,10))
#         print("send_form_data_to_remoteurl: {0} ".format(r.text))
#     except (requests.exceptions.RequestException, requests.exceptions.ReadTimeout) as exp:
#         print("send_form_data_to_remoteurl exceptions: {0} ".format(exp))
#
#     #print(r.text)
#     return 0


class StmPlanTask(Task):
    """
    this class based task is replacing get_stm_plan_task function based task. 
    run() method is executed when this task executed from queue
    
        :param session_key: str: key when a session is created
        :param form_data: quote request form data from plan.html
        :return: zero
    """

    # selection_data = {preference_data} - {completed_data}
    def run(self, session_key, form_data, selection_data=None, *args, **kwargs):
        threaded_request(copy.deepcopy(form_data), session_key, copy.deepcopy(selection_data))


class LimPlanTask(Task):
    """
        :param session_key: str: key when a session is created
        :param form_data: quote request form data from plan.html
        :return: zero
    """

    def run(self, session_key, form_data, *args, **kwargs):
        threaded_request(copy.deepcopy(form_data), session_key)


class AncPlanTask(Task):
    """
        :param session_key: str: key when a session is created
        :param form_data: quote request form data from plan.html
        :return: zero
    """

    def run(self, session_key, form_data, *args, **kwargs):
        threaded_request(copy.deepcopy(form_data), session_key)


def only_one(function=None, ikey="", timeout=None):
    """Enforce only one celery task at a time."""

    def _dec(run_func):
        """Decorator."""

        def _caller(*args, **kwargs):
            """Caller."""
            ret_value = None
            have_lock = False

            key = kwargs.get('keytask', ikey)
            lock = REDIS_CLIENT.lock(key, timeout=timeout)

            try:
                have_lock = lock.acquire(blocking=False)
                if have_lock:
                    print('Lock Acquired: {0}'.format(key))
                    ret_value = run_func(*args, **kwargs)
                else:
                    print('Failed to Acquire Lock: {0}'.format(key))
            finally:
                if have_lock:
                    lock.release()
                    print('Lock Closed: {0}'.format(key))

            return ret_value

        return _caller

    return _dec(function) if function is not None else _dec


class EsignCheckBeat(PeriodicTask):
    """
    E-sign check beat
    """

    run_every = timedelta(seconds=settings.CELERY_ESIGN_CHECK_TIME)

    def run(self, **kwargs):
        print('beat')

        now = timezone.now()
        today = now.date()
        next_esign_check_time = now - timedelta(seconds=settings.CELERY_NEXT_ESIGN_CHECK_TIME)
        # for stm_enroll_obj in StmEnroll.objects.filter(Q(enrolled=False, esign_verification_starts=True, # TODO
        #                                                  esign_verification_pending=True,
        #                                                  esign_verification_applicant_info__isnull=False,
        #                                                  esign_completed=False, Effective_Date__gt=today),
        #                                                Q(last_esign_checked_at__isnull=True) |
        #                                                        Q(last_esign_checked_at__lte=next_esign_check_time))[:5]:
        #     print(stm_enroll_obj)
        #     vimm_enroll_id = stm_enroll_obj.vimm_enroll_id
        #     keytask = 'generate_esign_check_key-{0}'.format(vimm_enroll_id)
        #     EsignCheckWorker.delay(vimm_enroll_id, keytask=keytask)


# class EsignCheckWorker(Task):
#     """
#     E-sign check worker, checks if the user signed the plan terms to enroll.
#     """
#
#     @only_one(ikey="generate_esign_check", timeout=settings.CELERY_TASK_LOCK_EXPIRE)
#     def run(self, vimm_enroll_id, keytask='generate_esign_check_key'):
#         stm_enroll_obj = StmEnroll.objects.get(vimm_enroll_id=vimm_enroll_id)
#         print('worker')
#         print(stm_enroll_obj.vimm_enroll_id)
#         customer_esigned = check_esign(stm_enroll_obj)
#         print(customer_esigned)


# def update_addon_plan_at_enroll(stm_enroll_obj, add_ons):
#     fields = ['Member_ID']
#     for add_on in add_ons:
#         try:
#             add_on_obj = stm_enroll_obj.addonplan_set.get(addon_id=add_on['ID'], carrier_name=add_on['Name'])
#             add_on_obj.Member_ID = add_on.get('Member_ID', None)
#             add_on_obj.save(update_fields=fields)
#         except ObjectDoesNotExist as err:
#             print(err)
#     return stm_enroll_obj


# def save_enrolled_applicant_info(stm_enroll_obj, enrolled_applicant_info, enrolled=True):
#     fields = ['Member_ID', 'Payment_Status_Date', 'Password', 'User_ID',
#               'Status', 'ApplicantID', 'LoginURL', 'enrolled']
#
#     for field in fields:
#         if field in ['Payment_Status_Date']:
#             setattr(stm_enroll_obj, field, QR_DATE_PATTERN.sub(r'\3-\1-\2', enrolled_applicant_info.get(field, '')))
#             continue
#         setattr(stm_enroll_obj, field, enrolled_applicant_info.get(field, None))
#
#     stm_enroll_obj.enrolled = True
#     stm_enroll_obj.save(update_fields=fields)
#
#     if stm_enroll_obj.addonplan_set.count() and enrolled_applicant_info.get('Add_ons', None):
#         update_addon_plan_at_enroll(stm_enroll_obj, enrolled_applicant_info.get('Add_ons', []))
#     return stm_enroll_obj


# def check_esign(stm_enroll_obj):
#     print('Hii plan esign check...')
#     fields_to_update_on_hii_enrollment = []
#     esign_res = json_decoder.decode(stm_enroll_obj.esign_verification_applicant_info or '{}')
#     if not esign_res:
#         return None
#
#     res2_formatted = None
#     # TODO Implement post date
#     # if stm_enroll_obj.is_post_date:
#     #     try:
#     #         res1 = esign_res.split('</Result>', 1)[0] + '</Result>'
#     #         res2 = esign_res.split('</Result>', 1)[1]
#     #         if res2.strip():
#     #             try:
#     #                 res2_formatted = ESignResponse(res2, request=request_user_info)
#     #             except ParseError as err:
#     #                 logger.warning("Esign Verification payment res2 parse error: {0}".format(err),
#     #                                user_info=request_user_info, log_vimm_enroll_id=vimm_enroll_id)
#     #                 res1 = esign_res
#     #         esign_res = res1
#     #     except IndexError:
#     #         pass
#
#     formatted_esign_response = ESignResponse(esign_res)  # , request=request_user_info)
#
#     if not formatted_esign_response.applicant:
#         return None
#
#     attr_data = {
#         'Quote_ID': formatted_esign_response.applicant['Quote_ID'],
#         'ApplicantID': formatted_esign_response.applicant['ApplicantID'],
#         'Access_Token': formatted_esign_response.applicant['Access_Token'],
#         'Process_Option': 'payment'
#     }
#
#     esign_enroll = ESignVerificationEnroll(attr_data=attr_data)
#     try:
#         res = esign_enroll.get_response()
#     except requests.exceptions.RequestException as err:
#         return None
#
#     # storing last esign checked time
#     stm_enroll_obj.last_esign_checked_at = timezone.now()
#     stm_enroll_obj.save(update_fields=['last_esign_checked_at'])
#
#     hii_formatted_enroll_response = res and EnrollResponse(res)
#     if hii_formatted_enroll_response.applicant:
#         print(hii_formatted_enroll_response.applicant)
#         stm_enroll_obj.enrolled_plan_res = json_encoder.encode(res)
#         fields_to_update_on_hii_enrollment.append('enrolled_plan_res')
#
#         stm_enroll_obj.esign_verification_pending = False
#         stm_enroll_obj.processed = True
#         stm_enroll_obj.processed_at = timezone.now()
#         stm_enroll_obj.esign_completed = True
#         stm_enroll_obj.esign_checked_and_enrolled_by_system = True
#         fields_to_update_on_hii_enrollment.extend(['esign_verification_pending', 'processed', 'processed_at',
#                                                    'esign_completed', 'esign_checked_and_enrolled_by_system'])
#         stm_enroll_obj.save(update_fields=fields_to_update_on_hii_enrollment)
#         save_enrolled_applicant_info(stm_enroll_obj, hii_formatted_enroll_response.applicant, enrolled=True)
#
#         return True
#
#     else:
#         return False



# TODO: Need Documentation and Unittest
def get_api_rate_data(carrier_obj, data, request_options=None, request=None):
    """

    :param carrier_obj: django model object
    :param data: dict type
    :param request_options:
    :param request:
    :return: list obj
    """
    try:
        rate_cls = PROVIDERS[carrier_obj.name]
    except KeyError as error:
        print(f"provider class not found with Carrier_ID: {carrier_obj.id}; Error: {error}")
        return []
    payload_data = copy.deepcopy(data)
    payload_data['Plan_ID'] = carrier_obj.plan_id
    return rate_cls.all_rates(data=data, ins_type=data['Ins_Type'], plan_id=carrier_obj.plan_id, request_options=None, request=None)


# TODO: Need Documentation and Unittest
def get_api_rate_obj(payload, form_data, ins_type, cls_name, plan_id, carrier_name):
    """

    :param payload:
    :param form_data:
    :param product_type:
    :param product_ids:
    :param cls_name:
    :param plan_id:
    :param api_source:
    :param verification_weight:
    :param has_post_date_api:
    :return:
    """
    print(f'plan_id: {plan_id}, ins_type: {ins_type}')

    try:
        rate_cls = PROVIDERS[carrier_name]
    except KeyError as err:
        print(f'provider class not found with Carrier ID: {plan_id}, Error: {err}')
        return []
    print("rate_cls: {}; cls_name: {}".format(rate_cls.__class__.__name__, cls_name))


    return rate_cls(**payload)


# TODO: Need Documentation and Unittest
def prepare_tasks(form_data, ins_type, session_identifier_quote_store_key, request_options=None, request=None, api_sources=None):
    """

    :param form_data:
    :param session_quote_store_key:
    :param request_options:
    :param request:
    :param api_sources:
    :return:
    """
    rate_requests = []
    try:
        carriers = Carrier.objects.filter(
            is_active=True,
            allowed_state__contains=form_data['State'],
            ins_type=ins_type
        )
    except Carrier.DoesNotExist as err:
        return False

    # TODO: Handle non stm states.

    for carrier in carriers:
        rate_requests += get_api_rate_data(carrier, form_data, request_options=request_options, request=request)

    if not rate_requests:
        return False

    redis_keys = []

    for idx, task_data in enumerate(rate_requests):
        redis_key = "{}#{}".format(session_identifier_quote_store_key, uuid.uuid4())
        redis_keys.append(redis_key)
        ProcessTask.delay(task_data, redis_key)

    request.session[session_identifier_quote_store_key] = redis_keys
    request.session['{}##status'.format(session_identifier_quote_store_key)] = 'processing'
    print('redis_keys: {}'.format(redis_keys))
    return True



# TODO: Need Documentation and Unittest
def post_process_task(data, session_identifier_quote_store_key, request):
    """

    :param data:
    :param session_identifier_quote_store_key:
    :param request:
    :return:
    """
    redis_keys = request.session.get(session_identifier_quote_store_key)

    results = {
        "stm_plans": [],
        "sorting_conditions": {}
    }

    addon_plans = {}
    sorting_conditions = {}
    errors = []
    for redis_key in redis_keys:
        content = REDIS_CLIENT.get(redis_key)
        print(f'content: {content}, for key: {redis_key}')
        if content:
            content = json_decoder.decode(content.decode())
            results['stm_plans'] += content.get("main_plans", [])

            error = content.get("error", [])
            if 'api_error' in error:
                errors.append("Failed to access API for Plan {}".format(content['plan_name']))
                print("api_error")
                continue
            else:
                addon_list_of_dict = content.get("addon_plans", [])
                plan_name = content['plan_name']
                addon_plan_redis_key = "{0}:{1}".format(session_identifier_quote_store_key, plan_name.lower().replace(" ", '-'))
                new_addon_plans = new_addon_plan_to_add(
                    addon_plans_from_json_data(REDIS_CLIENT.lrange(addon_plan_redis_key, 0, -1)),
                    set(addon_plans_from_dict(addon_list_of_dict))
                )
                for new_addon_plan in new_addon_plans:
                    REDIS_CLIENT.rpush(addon_plan_redis_key, new_addon_plan)
            continue
        return 'processing'
    else:
        if data['Ins_Type'] == 'stm':
            for plan_data in results['stm_plans']:
                try:
                    sc_cp = sorting_conditions['CP']
                except KeyError:
                    sorting_conditions['CP'] = []
                    sc_cp = sorting_conditions['CP']
                finally:
                    if plan_data['Coinsurance_Percentage'] not in sc_cp:
                        sc_cp.append(plan_data['Coinsurance_Percentage'])

                try:
                    sc_moop = sorting_conditions['MOOP']
                except KeyError:
                    sorting_conditions['MOOP'] = []
                    sc_moop = sorting_conditions['MOOP']
                finally:
                    if plan_data['out_of_pocket_value'] not in sc_moop:
                        sc_moop.append(plan_data['out_of_pocket_value'])

                try:
                    sc_cm = sorting_conditions['CM']
                except KeyError:
                    sorting_conditions['CM'] = []
                    sc_cm = sorting_conditions['CM']
                finally:
                    if plan_data['coverage_max_value'] not in sc_cm:
                        sc_cm.append(plan_data['coverage_max_value'])

        if sorting_conditions:
            sorting_conditions['CP'].sort(key=lambda v: - int(v))
            sorting_conditions['MOOP'].sort(key=lambda v: - int(v))
            sorting_conditions['CM'].sort(key=lambda v: - int(v))

        #results['addon_plans'] = {data['plan_name_for_img']: addon_plans}
        results['sorting_conditions'] = sorting_conditions
        if errors:
            results['errors'] = errors
        print('--------\n\n\ncontents: {}\n\n\n-------'.format(results))

        REDIS_CLIENT.setex(name=session_identifier_quote_store_key,
                           value=json_encoder.encode(results),
                           time=timedelta(hours=24))
        request.session['{}##status'.format(session_identifier_quote_store_key)] = 'complete'
        request.session.modified = True
        for redis_key in redis_keys:
            REDIS_CLIENT.delete(redis_key)

    return 'complete'


class ProcessTask(Task):
    # TODO: Need documentation and Unittest
    def run(self, task_data, redis_key):
        form_data = task_data['form_data']
        main_plans = []
        addon_plans = []
        error = []
        fetched_data = {
            "plan_name": "",
            "main_plans": [],
            "addon_plans": [],
            "filtering_conditions": [],
            "error": []
        }
        print(f'task_data: {task_data}')
        try:
            task_obj = get_api_rate_obj(**task_data)
        except KeyError as err:
            print(f'API source map obj not found for api_source: {task_data["api_source"]}')
            REDIS_CLIENT.setex(
                name=redis_key,
                time=timedelta(hours=2),
                value=json_encoder.encode(fetched_data)
            )
            return False
        print('task_obj: {}'.format(task_obj.__class__))
        task_obj.process_response()

        res = task_obj.get_formatted_response()
        if res:
            # set task.api_error for HII
            # if no main plan and no add_plan
            # having error in api response
            if not res.monthly and not res.addon_plans and res.errors:
                task_obj.api_error = True

            for monthly_plan in res.monthly:
                data = monthly_plan.get_data_as_dict()
                # if task_obj.product_type == 'add_on':
                #     addon_plans.append(data)
                #     continue
                main_plans.append(data)
            if res.addon_plans:
                for addon_plan in res.addon_plans:
                    addon_plans.append(addon_plan.data_as_dict())

        # important for showing error message related to API call
        # to the user (agent or verifier)
        if task_obj.api_error:
            error.append('api_error')

        fetched_data.update({
            "plan_name": task_obj.Name,
            "main_plans": main_plans,
            "addon_plans": addon_plans,
            "filtering_conditions": [],
            "error": error
        })
        print('addon_plans: {}'.format(addon_plans))
        print("saving content: {} , for key {}".format(fetched_data, redis_key))
        REDIS_CLIENT.setex(
            name=redis_key,
            time=timedelta(hours=24),
            value=json_encoder.encode(fetched_data)
        )
        return True