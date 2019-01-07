from __future__ import unicode_literals, print_function

from .utils import form_data_is_valid
import quotes.models as qm
from django.core.exceptions import ObjectDoesNotExist

# For static type checking.
from django.http.request import HttpRequest


def hp_context(request):
    try:
        quote_request_form_data = request.session['quote_request_form_data']
        premium_factor = 1

        if quote_request_form_data["Include_Spouse"] == 'Yes':
            premium_factor += 0.70

        if quote_request_form_data["Children_Count"]:
            for child in quote_request_form_data["Dependents"]:
                if child["Child_Age"] >= 18:
                    premium_factor += 0.7
                else:
                    premium_factor += 0.4

        premium_factor = int(round(premium_factor))

        if quote_request_form_data['Ins_Type'] == 'stm':
            premium_list = (('0', str(100 * premium_factor)),
                            (str(100 * premium_factor), str(150 * premium_factor)),
                            (str(150 * premium_factor), str(200 * premium_factor)),
                            (str(250 * premium_factor), str(300 * premium_factor)),
                            (str(300 * premium_factor), '1000000000'))

        elif quote_request_form_data['Ins_Type'] == 'lim':
            premium_list = (('0', str(50 * premium_factor)),
                            (str(50 * premium_factor), str(80 * premium_factor)),
                            (str(80 * premium_factor), str(100 * premium_factor)),
                            (str(100 * premium_factor), str(200 * premium_factor)),
                            (str(200 * premium_factor), '1000000000'))

        elif quote_request_form_data['Ins_Type'] == 'anc':
            premium_list = (('0', str(20 * premium_factor)),
                            (str(20 * premium_factor), str(40 * premium_factor)),
                            (str(40 * premium_factor), str(60 * premium_factor)),
                            (str(60 * premium_factor), str(80 * premium_factor)),
                            (str(80 * premium_factor), '1000000000'))

    except KeyError as k:
        print("Context processor: No suitable form data.", k)

        premium_list = (('0', '50'), ('50', '80'), ('80', '100'),
                        ('100', '200'), ('200', '1000000000'))

    return {
        # 'ctx_company_list': (('109', 'Everest STM'), ('67', 'HealtheFlex STM'), ('56', 'HealtheMed STM'),
        #                      ('89', 'Premier STM'), ('104', 'Sage STM')),
        'ctx_company_list': (
            # ('54', 'Principle Advantage'),
            # ('104', 'Sage STM'),
            ('48', 'Foundation Dental'),
            ('64', 'Freedom Spirit Plus'),
            ('88', 'Safeguard Critical Illness'),
            ('109', 'Everest STM'),
            ('112', 'LifeShield STM'),
            ('122', 'Legion Limited Medical'),
            ('136', 'Cardinal Choice'),
            ('152', 'Health Choice'),
            ('151', 'USA Dental'),
            ('153', 'Vitala Care'),
            ('209', 'AdvantHealth STM'),

            # ('97', 'Select STM'),
            # ('90', 'Unified Health One')
        ),
        'ctx_stm_company_list': (
            ('109', 'Everest STM'),
            ('112', 'LifeShield STM'),
            ('209', 'AdvantHealth STM'),
        ),
        'ctx_lim_company_list': (
            ('122', 'Legion Limited Medical'),
            ('136', 'Cardinal Choice'),
            ('152', 'Health Choice'),
            ('153', 'Vitala Care')
        ),

        'ctx_anc_company_list': (
            ('48', 'Foundation Dental'),
            ('64', 'Freedom Spirit Plus'),
            ('88', 'Safeguard Critical Illness'),
            ('151', 'USA Dental')
        ),

        'ctx_monthly_premium_list': premium_list,

        'ctx_deductible_option_list': ('250', '500', '1000', '2500',
                                       '5000', '7500', '10000'),
        'ctx_coinsurance_limit_list': ('0', '20', '30', '50'),
        'ctx_max_out_of_pocket_list': (('0', '3500'), ('3500', '6500'), ('6500', '10000'),
                                       ('10000', '20000'), ('20000', '10000000')),
        'ctx_policy_maximum_list': ('50000', '100000', '250000', '500000',
                                    '750000', '1000000', '1500000', '2000000'),
    }

# def hp_ongoing_app_exists(request: HttpRequest) -> dict:
#     """Here are creating a context processor which returns a dictionary
#     If session contains the key, value pair of 'ctx_app_url_exists': True, and,
#     if there is a 'ongoing_session_plan_url' in session and also,
#     if quote_request_form_data is valid.
#
#     :param request: Django HttpRequest object
#     :return: bool
#     :returns: true if application exist
#     """
#     try:
#         if request.session['ongoing_session_plan_url']:
#             plan_url = request.session['ongoing_session_plan_url']
#             vimm_enroll_id = plan_url.rsplit('-', 1)[-1]
#             esign_has_been_sent = False
#             try:
#                 stm_enroll_obj = qm.StmEnroll.objects.get(vimm_enroll_id=vimm_enroll_id)
#                 esign_has_been_sent = stm_enroll_obj.esign_verification_starts or\
#                                       stm_enroll_obj.esign_verification_pending
#             except (ObjectDoesNotExist, AttributeError) as err:
#                 print("Context processor - obj does not exist in database.", err)
#             # session = request.session.get(plan_url)
#             stage = request.session['ongoing_session_stage']
#             quote_request_form_data = request.session.get('{0}_form_data'.format(plan_url), {})
#             if form_data_is_valid(quote_request_form_data) and not esign_has_been_sent:
#                 return {
#                     'ctx_app_url': plan_url,
#                     'ctx_unique_url_stage': reverse('healthplans:stm_enroll', args=[plan_url, stage]),
#                     'ctx_app_url_exists': True,
#                     # 'ctx_app_stage': stage
#                 }
#     except KeyError as k:
#         print("Context processor, no saved plan URL", k)
#
#
#     return {
#         'ctx_app_url_exists': False
#     }
