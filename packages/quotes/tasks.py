from __future__ import absolute_import, unicode_literals

import re
import os
import copy
# import time
import json
import redis
import requests

from datetime import timedelta

from geoip2 import database as geo_database

from celery import shared_task
from celery.task import PeriodicTask, Task
from celery.utils.log import get_task_logger

# from quotes.mail import send_mail
from quotes.quote_thread import threaded_request
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

    def run(self, session_key, form_data, *args, **kwargs):
        threaded_request(copy.deepcopy(form_data), session_key)


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

