import copy
import json
from urllib import request

import requests

from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse, HttpRequest, Http404, HttpResponse
from django.shortcuts import render
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from core import settings
from quotes.forms import QR_DATE_PATTERN
from quotes.templatetags.hp_tags import plan_actual_premium
from .forms import (AppAnswerForm, AppAnswerCheckForm, StageOneTransitionForm, STApplicantInfoForm, STParentInfo,
                    STDependentInfoFormSet, PaymentMethodForm, GetEnrolledForm, AddonPlanForm, ApplicantInfoForm,
                    ChildInfoFormSet, LeadForm, AjaxRequestAttrChangeForm,
                    AjaxRequestAttrChangeForm, DurationCoverageForm)
from .question_request import get_stm_questions
from .quote_thread import addon_plans_from_dict, addon_plans_from_json_data, threaded_request
from .redisqueue import redis_connect
from .utils import (form_data_is_valid, get_random_string, get_app_stage, get_askable_questions,
                    update_applicant_info, save_applicant_info, update_application_stage,
                    save_stm_plan, save_dependent_info, update_dependent_info,
                    save_add_on_info, get_initials_for_dependents_formset, save_applicant_payment_info, log_user_info,
                    save_enrolled_applicant_info, get_st_dependent_info_formset, get_quote_store_key, save_lead_info,
                    update_lead_vimm_enroll_id, update_leads_stm_id, create_selection_data,
                    get_dict_for_available_alternate_plans, get_available_coins_against_benefit,
                    get_available_benefit_against_coins, get_neighbour_plans_and_attrs)
from .logger import VimmLogger
from .tasks import StmPlanTask, LimPlanTask, AncPlanTask
from .enroll import Enroll, Response as EnrollResponse, ESignResponse, ESignVerificationEnroll

import quotes.models as qm

# For type annotation
from django.core.handlers.wsgi import WSGIRequest
from typing import Union, List, Dict, Any, Optional

logger = VimmLogger('quote_turbo')

json_decoder = json.JSONDecoder()
json_encoder = json.JSONEncoder()
redis_conn = redis_connect()

def get_prop_context():
    """Return context variables for the home and plans view

    :param prop: User attributes
    :return: context variables
    """
    props = settings.USER_PROPERTIES
    prop_context = {
        'applicant_min_age': props['min_age'],
        'applicant_max_age': props['max_age'],

        'spouse_min_age': props['min_age'],
        'spouse_max_age': props['max_age'],

        'dependents_min_age': props['dependents_min_age'],
        'dependents_max_age': props['dependents_max_age']
    }

    return prop_context

def home(request: WSGIRequest) -> HttpResponse:
    prop =settings.USER_PROPERTIES


    return render(request, 'homepage.html', get_prop_context())


def plans(request: WSGIRequest, zip_code=None) -> HttpResponse:
    """View is handled in whole entiarity in vuejs.

    This view is maybe not needed. 

    :param request: Django request object
    :return: Django HttpResponse Object
    """
    return render(request, 'quotes/../../templates/homepage.html', get_prop_context())


@require_POST
def validate_quote_form(request: WSGIRequest) -> JsonResponse:
    """
    Returns success if successfully started celery.
    Errors if there are form errors.

    :param request: Django request object
    :return: Django JsonResponse Object
    """
    print(f" ------------\n| POST DATA  |:\n ------------\n{request.POST}")

    form = ApplicantInfoForm(request.POST)
    formset = ChildInfoFormSet(request.POST)
    if not request.session.exists(request.session.session_key):
        request.session.create()
    request.session['applicant_enrolled'] = False
    request.session.modified = True
    if form.is_valid() and formset.is_valid():
        logger.info("quote info form is valid")
        print("quote info form is valid")
        quote_request_form_data = form.cleaned_data

        if quote_request_form_data.get('applicant_is_child', True):
            logger.info("applicant is child - making sure there is no dependents")
            quote_request_form_data['Dependents'] = []
            quote_request_formset_data = []
        else:
            quote_request_formset_data = formset.cleaned_data
            logger.info("dependents info to quote request form data")
            quote_request_form_data['Dependents'] = quote_request_formset_data

        quote_request_form_data['quote_store_key'] = get_quote_store_key(copy.deepcopy(quote_request_form_data))
        logger.info(f"quote_request_form_data['quote_store_key'] <--- {quote_request_form_data['quote_store_key']}")

        request.session['quote_request_form_data'] = quote_request_form_data
        request.session['quote_request_formset_data'] = quote_request_formset_data
        request.session['quote_request_response_data'] = {}

        lead_form = LeadForm(quote_request_form_data)
        if lead_form.is_valid():
            print("lead form is valid")
            logger.info("saving lead info")
            lead_form.save()
        else:
            print(f'----------------\nLead Form Errors :\n----------------\n{lead_form.errors}')

        # Saving Lead Form Info
        save_lead_info(qm.Leads, lead_form.cleaned_data)
        
        start_celery_return_code = start_celery(request, quote_request_form_data)

        if start_celery_return_code:
            return JsonResponse({
                'status': 'success',
            })

    else:
        print(form.errors)
        print(formset.errors)
        return JsonResponse(
            {
                'status': 'false',
                'error': "Failed",
                "errors": dict(form.errors.items()),
                "error_keys": list(form.errors.keys()),
                "formset_errors": formset.errors
            }
        )


def start_celery(request: WSGIRequest, form_data: Dict) -> True:
        """
        """

        if form_data and form_data_is_valid(form_data) == False:
            form_data = {}
            request.session['quote_request_form_data'] = {}
            request.session['quote_request_formset_data'] = []
            request.session['quote_request_response_data'] = {}

        logger.info("Plan Quote For Data: {0}".format(form_data))

        d: Dict[str, List[str]] = {'monthly_plans': [], 'addon_plans': []}
        request.session['quote_request_response_data'] = d
        request.session.modified = True
        logger.info("PLAN QUOTE LIST - form data: {0}".format(form_data))

        print('------------------------\nquote_request_form_data: \n------------------------')
        print(json.dumps(form_data, indent=4, sort_keys=True))

        # Changing quote store key regarding insurance type
        for ins_type in ['lim', 'stm']:
        #     ins_type = get_ins_type(request)
            change_quote_store_key(request, ins_type)
            form_data['Ins_Type'] = ins_type

            # Calling celery for populating quote list
            redis_key = get_redis_key(request, ins_type)
            print(f"Calling celery task for ins_type: {ins_type}")
            print(f"redis_key: {redis_key}")

            if not redis_conn.exists(redis_key):
                print("Redis connection does not exist for redis key")
                redis_conn.rpush(redis_key, *[json_encoder.encode('START')])

                print(f"Insurance type is {ins_type}")
                if ins_type == 'stm':
                    redis_key_done_data = f'{redis_key}:done_data'
                    # We are here setting up a dictionary in the session for future usage
                    print(f'Setting quote request preference data')

                    quote_request_preference_data = copy.deepcopy(settings.USER_INITIAL_PREFERENCE_DATA)

                    quote_request_done_data: Dict[str, Dict[str, List[str]]] = {
                        'LifeShield STM': {
                            'Duration_Coverage': [],
                        },

                        'AdvantHealth STM': {
                            'Duration_Coverage': []
                        }
                    }

                    request.session['quote_request_preference_data'] = quote_request_preference_data

                    redis_conn.set(redis_key_done_data, json.dumps(quote_request_done_data))

                    StmPlanTask.delay(request.session.session_key, form_data,
                                      quote_request_preference_data)

                elif ins_type == 'lim':
                    LimPlanTask.delay(request.session.session_key, form_data)

        return True


def get_ins_type(request: WSGIRequest) -> str:
    ins_type = request.COOKIES.get('qt_plan_type', None)

    if not ins_type:
        ins_type = 'lim'

    return ins_type


def set_ins_type_in_session(request: WSGIRequest, ins_type: str) -> None:
    quote_request_form_data = request.session.get('quote_request_form_data', None)
    quote_request_form_data['Ins_Type'] = ins_type
    request.session['quote_request_form_data'].update(quote_request_form_data)

    return


def set_annual_income_and_redirect_to_plans(request: WSGIRequest) -> JsonResponse:
    """

    :return: JsonResponse containing the url
    """
    quote_request_form_data = request.session.get('quote_request_form_data')
    ins_type = get_ins_type(request)
    set_ins_type_in_session(request, ins_type)
    quote_request_form_data = request.session.get('quote_request_form_data', None)

    print(f" ------------\n| ANNUAL INCOME DATA  |:\n ------------\n{request.POST}")
    annual_income = request.POST.get('Annual_Income', None)

    if annual_income and quote_request_form_data:
        quote_request_form_data['Annual_Income'] = annual_income

        quote_request_preference_data = request.session.get('quote_request_preference_data', None)

        if quote_request_preference_data:
            for plan_name in ['LifeShield STM', 'AdvantHealth STM']:
                quote_request_preference_data[plan_name]['Coverage_Max'] = \
                    [policy_max_from_income(int(quote_request_form_data['Annual_Income']), plan_name)]

        request.session['quote_request_preference_data'] = quote_request_preference_data

        response = {
            'status': 'success',
            'url': reverse('quotes:plan_quote', kwargs={'ins_type': ins_type})
        }
    else:
        response = {
            'status': 'fail',
            'error': "Failed",
        }

    return JsonResponse(response)


def survey_members(request):
    return render(request, 'quotes/survey/members.html', {})


def policy_max_from_income(income: int, plan_name: str) -> str:
    """
    We shall take these dictionary to settings file.

    :param income: Annual Income
    :return: Coverage/Policy Maximum
    """

    # 'policy_max_dict' is a dictionary which has been hardcoded to return values against
    # low medium and High.
    policy_max_dict = settings.CARRIER_SPECIFIC_INCOME_VS_POLICY_MAXIMUM

    income_low_point = 30000
    income_high_point = 47000

    if income_low_point >= income:
        return policy_max_dict[plan_name]['low']

    elif income_high_point > income > income_low_point:
        return policy_max_dict[plan_name]['medium']

    elif income >= income_high_point:
        return policy_max_dict[plan_name]['high']

    # TODO: Return a None and handle it.


def reset_preference(request) -> None:
    """
    Reset everything but duration coverage and coverage max.
    :param request:
    :return:
    """
    preference =  request.session.get('quote_request_preference_data', None)

    form_data = request.session.get('quote_request_form_data', None)
    income = int(form_data['Annual_Income'])

    if preference is None:
        return
    stm_carriers = ['LifeShield STM', 'AdvantHealth STM'] # TODO: USE SETTINGS VAR
    duration_coverage, coverage_max = {}, {}
    for carrier in stm_carriers:
        duration_coverage[carrier] = preference[carrier]['Duration_Coverage']
        try:
            coverage_max[carrier] = [policy_max_from_income(income, carrier)]
        except KeyError as k:
            coverage_max[carrier] = [preference[carrier]['Coverage_Max']]

    preference = copy.deepcopy(settings.USER_INITIAL_PREFERENCE_DATA)

    for carrier in stm_carriers:
        preference[carrier]['Duration_Coverage'] = duration_coverage[carrier]
        preference[carrier]['Coverage_Max'] = coverage_max[carrier]

    request.session['quote_request_preference_data'] = preference

    return


def plan_quote(request, ins_type):
    """Show a large list of plans to to the user.

    :param request: Django request object
    :param ins_type: stm/lim/anc
    :return: Django HttpResponse Object
    """
    try:
        if ins_type == 'stm':
            reset_preference(request)
            request.session['stm_general_url_chosen'] = False
    except KeyError:
        print("User preference not found")
        pass

    quote_request_form_data = request.session.get('quote_request_form_data', {})


    request.session['applicant_enrolled'] = False
    request.session.modified = True
    if quote_request_form_data.get('applicant_is_child', True):
        request.session['quote_request_formset_data'] = []

    if quote_request_form_data and form_data_is_valid(quote_request_form_data) == False:
        quote_request_form_data = {}
        request.session['quote_request_form_data'] = {}
        request.session['quote_request_formset_data'] = []
        request.session['quote_request_response_data'] = {}

    if not quote_request_form_data:
        return HttpResponseRedirect(reverse('quotes:plans', args=[]))

    logger.info("Plan Quote For Data: {0}".format(quote_request_form_data))

    d = {'monthly_plans': [], 'addon_plans': []}
    request.session['quote_request_response_data'] = d
    request.session.modified = True
    logger.info("PLAN QUOTE LIST - form data: {0}".format(quote_request_form_data))


    change_quote_store_key(request, ins_type)
    quote_request_form_data = request.session.get('quote_request_form_data', {})

    request.session['quote_request_form_data']['Ins_Type'] = ins_type # TODO: functionify

    print('------------------------\nquote_request_form_data: \n------------------------')
    print(json.dumps(quote_request_form_data, indent=4, sort_keys=True))

    return render(request, 'quotes/quote_list.html', {
        'form_data': quote_request_form_data, 'xml_res': d
    })


def change_quote_store_key(request: WSGIRequest, ins_type: str) -> None:
    """
    Changing quote store key regarding insurance type
    NOT currently being used.
    """
    quote_request_form_data = request.session.get('quote_request_form_data', {})
    if not quote_request_form_data:
        return
    quote_store_key = quote_request_form_data['quote_store_key']

    if is_ins_type_valid(ins_type):
        quote_store_key = quote_store_key[:-3] + ins_type
        quote_request_form_data['quote_store_key'] = quote_store_key

    request.session['quote_request_form_data'].update(quote_request_form_data)

    return None


def stm_plan(request: WSGIRequest, plan_url: str) -> HttpResponse:
    """Show currently selected plan to user for application. Also select addons.

    :param request: Django request object
    :param plan_url: Unique url for plan that sits in plan_data
    :return: HttpResponse
    """
    stm_carriers = copy.deepcopy(settings.TYPEWISE_PLAN_LIST['stm'])

    logger.info(f"Plan details: {plan_url}")

    quote_request_form_data = request.session.get('quote_request_form_data', {})
    quote_request_preference_data = request.session.get('quote_request_preference_data', {})

    ins_type = quote_request_form_data.get('Ins_Type', None)
    request.session['quote_request_form_data'].update(quote_request_form_data)

    request.session['applicant_enrolled'] = False
    if quote_request_form_data and form_data_is_valid(quote_request_form_data) == False:
        quote_request_form_data = {}
        request.session['quote_request_form_data'] = {}
        request.session['quote_request_formset_data'] = []
        request.session.modified = True

    if not quote_request_form_data:
        return HttpResponseRedirect(reverse('quotes:plans', args=[]))

    plan_list = []
    redis_key = get_redis_key(request, ins_type)

    for plan in redis_conn.lrange(redis_key, 0, -1):
        p = json_decoder.decode(plan.decode())
        if not isinstance(p, str):
            plan_list.append(p)

    if not plan_list:
        logger.warning("No Plan found: {0}; no plan for the session".format(plan_url))
        raise Http404()

    try:
        if ins_type == 'stm':
            stm_plan_unique_url = request.COOKIES.get('current-plan-unique-url')
            stm_plan_general_url = request.COOKIES.get('current-plan-general-url')
            if request.session['stm_general_url_chosen'] == False and stm_plan_general_url == plan_url:
                plan = next(filter(lambda mp : mp['unique_url'] == stm_plan_unique_url, plan_list))

                update_session_preferenced_data(
                    request=request,
                    stm_name=plan['Name'],
                    preference_for_current_stm=None,
                    coverage_duration=plan['Duration_Coverage'],
                    plan=plan
                )
            else:
                # When page is refreshed or duration coverage is changed.
                plan = next(filter(
                    lambda mp: mp['general_url'] == plan_url and
                        mp['coverage_max_value'] == quote_request_preference_data[mp['Name']]['Coverage_Max'][0] and
                        mp['Coinsurance_Percentage'] == quote_request_preference_data[mp['Name']]['Coinsurance_Percentage'][0] and
                        mp['out_of_pocket_value'] == quote_request_preference_data[mp['Name']]['Benefit_Amount'][0], plan_list))
                request.session['stm_general_url_chosen'] = True
        else:
            plan = next(filter(lambda mp: mp['unique_url'] == plan_url , plan_list))
    except StopIteration:
        logger.warning("No Plan Found: {0}; there are plans for this session".format(plan_url))
        raise Http404()
    except KeyError:
        logger.warning("No session preference data")
        raise Http404

    # Changing/Filtering the related plans here
    # Here option means deductible

    if plan['Name'] in stm_carriers:
        try:
            related_plans = list(filter(
                lambda mp: mp['Name'] == plan['Name'] and \
                           mp['option'] != plan['option'] and \
                           mp['Plan'] == plan['Plan'] and \
                           mp['Coinsurance_Percentage'] == quote_request_preference_data[mp['Name']]['Coinsurance_Percentage'][0] and \
                           mp['out_of_pocket_value'] == quote_request_preference_data[mp['Name']]['Benefit_Amount'][0] and \
                           mp['coverage_max_value'] == quote_request_preference_data[mp['Name']]['Coverage_Max'][0] and \
                           mp['Duration_Coverage'] == plan['Duration_Coverage'], sorted(plan_list, key=lambda x: x['Premium'])))
        except KeyError as k:
            print(k)
            pass

        available_alternatives_as_set = get_dict_for_available_alternate_plans(plan_list, plan) # TODO: Make it a part of separate function or at least modularize branching.
        neighbour_list, neighbour_attrs = get_neighbour_plans_and_attrs(plan, plan_list)
    else:
        related_plans = list(
            filter(lambda mp: mp['Name'] == plan['Name'] and mp['actual_premium'] != plan['actual_premium'], plan_list))

    logger.info(f'Number of RELATED PLANS: {len(related_plans)}')
    print('PLAN: ', plan)

    # addon plans
    selected_addon_plans = addon_plans_from_dict(
        request.session.get('{0}-{1}-{2}'.format(quote_request_form_data['quote_store_key'],
                                                 plan['unique_url'], "addon-plans"), [])
    )
    logger.info("no of selected addon plans: {0}, for plan: {1}".format(len(selected_addon_plans), plan['unique_url']))
    addon_plans_redis_key = "{0}:{1}".format(redis_key, plan['plan_name_for_img'])
    addon_plans = addon_plans_from_json_data(redis_conn.lrange(addon_plans_redis_key, 0, -1))
    remaining_addon_plans = addon_plans.difference(selected_addon_plans)

    # Duration coverage set literal. I shall move this to settings file or carrier model later.
    applicant_state_name = quote_request_form_data['State']
    plan_name = plan['Name']

    try:
        alternate_coverage_duration = copy.deepcopy(settings.STATE_SPECIFIC_PLAN_DURATION[plan_name][applicant_state_name])

        alternate_benefit_amount = list(neighbour_attrs['benefit_amount'])
        alternate_benefit_amount.sort(key=int)

        alternate_coinsurace_percentage = list(neighbour_attrs['coinsurance_percentage'])
        alternate_coinsurace_percentage.sort(key=int)

        # Edge case 50 percent coinsurance for plan type 2
        # if plan_name == 'LifeShield STM':
        #     if plan['Plan'] == '1':
        #         if '50' in alternate_coinsurace_percentage:
        #             alternate_coinsurace_percentage.remove('50')
        #         if '5000' in alternate_benefit_amount:
        #             alternate_benefit_amount.remove('5000')

        alternate_coverage_max = list(neighbour_attrs['coverage_maximum'])
        alternate_coverage_max.sort(key=int)

        alternate_plan_set = available_alternatives_as_set['alternate_plan'] - {plan['Plan']}
        alternate_plan = list(alternate_plan_set)


    except KeyError as k:
        print(f'{k} - No duration coverage for {plan_name}')
        alternate_coverage_duration = None
        alternate_benefit_amount = None
        alternate_coinsurace_percentage = None
        alternate_coverage_max = None
        alternate_plan = None

    carrier = None
    try:
        carrier = qm.Carrier.objects.get(plan_id=plan["Plan_ID"])
    except qm.Carrier.DoesNotExist as er:
        print("Very weird error: {}".format(er))

    return render(request,
                  # 'quotes/stm_plan.html',
                  'quotes/plans/{0}.html'.format(plan["Name"].lower().replace(' ', '_')),
                  {'plan': plan, 'related_plans': related_plans,
                   'quote_request_form_data': quote_request_form_data,
                   'addon_plans': addon_plans, 'selected_addon_plans': selected_addon_plans,
                   'remaining_addon_plans': remaining_addon_plans,
                   'alternate_coverage_duration': alternate_coverage_duration,
                   'alternate_benefit_amount': alternate_benefit_amount,
                   'alternate_coinsurace_percentage': alternate_coinsurace_percentage,
                   'alternate_coverage_max': alternate_coverage_max,
                   'alternate_plan': alternate_plan,
                   'benefit_amount_coinsurance_coverage_max_form': AjaxRequestAttrChangeForm,
                   'duration_coverage_form': DurationCoverageForm,
                   'benefit_coverage': qm.BenefitsAndCoverage.objects.filter(plan=carrier),
                   'restrictions_omissions': qm.RestrictionsAndOmissions.objects.filter(plan=carrier),
                   })


def stm_apply(request, plan_url) -> HttpResponse:
    quote_request_form_data = request.session.get('quote_request_form_data', {})
    request.session['applicant_enrolled'] = False
    request.session.modified = True
    if quote_request_form_data and form_data_is_valid(quote_request_form_data) == False:
        quote_request_form_data = {}
        request.session['quote_request_form_data'] = {}
        request.session['quote_request_formset_data'] = []

    if not quote_request_form_data:
        return HttpResponseRedirect(reverse('quotes:plans', args=[]))

    sp = []
    redis_key = "{0}:{1}".format(request.session._get_session_key(),
                                 quote_request_form_data['quote_store_key'])
    for plan in redis_conn.lrange(redis_key, 0, -1):
        p = json_decoder.decode(plan.decode())
        if not isinstance(p, str):
            sp.append(p)

    if not sp:
        logger.warning("No Plan found: {0}; no plan for the session".format(plan_url))
        raise Http404()

    try:
        plan = next(filter(lambda mp: mp['unique_url'] == plan_url, sp))
    except StopIteration:
        logger.warning("No Plan Found: {0}; there are plans for this session".format(plan_url))
        raise Http404()

    logger.info("apply for plan - {0}: {1}".format(plan_url, plan))

    selected_addon_plans = addon_plans_from_dict(
        request.session.get(
            '{0}-{1}-{2}'.format(quote_request_form_data['quote_store_key'], plan['unique_url'], "addon-plans"), [])
    )
    add_on_list_as_dict = [s_add_on_plan.data_as_dict() for s_add_on_plan in selected_addon_plans]
    logger.info("PLAN: {0}".format(plan))
    logger.info("ADD-ON: {0}".format(add_on_list_as_dict))

    # addon plans
    logger.info("no of selected addon plans: {0}, for plan: {1}".format(len(selected_addon_plans), plan['unique_url']))
    addon_plans_redis_key = "{0}:{1}".format(redis_key, plan['plan_name_for_img'])
    addon_plans = addon_plans_from_json_data(redis_conn.lrange(addon_plans_redis_key, 0, -1))
    remaining_addon_plans = addon_plans.difference(selected_addon_plans)

    return render(request, 'quotes/stm_plan_apply.html',
                  {'plan': plan, 'quote_request_form_data': quote_request_form_data,
                   'addon_plans': addon_plans,
                   'selected_addon_plans': selected_addon_plans,
                   'remaining_addon_plans': remaining_addon_plans,})


@require_POST
def stm_plan_addon_action(request, plan_url, action) -> Union[HttpResponseRedirect, JsonResponse]:
    logger.info("stm_plan_include_addon for plan {0}".format(plan_url))
    quote_request_form_data = request.session.get('quote_request_form_data', {})
    request.session['applicant_enrolled'] = False
    if quote_request_form_data and form_data_is_valid(quote_request_form_data) == False:
        quote_request_form_data = {}
        request.session['quote_request_form_data'] = {}
        request.session.modified = True

    if not quote_request_form_data:
        return HttpResponseRedirect(reverse('quotes:plans', args=[]))

    sp = []
    redis_key = "{0}:{1}".format(request.session._get_session_key(), quote_request_form_data['quote_store_key'])
    for plan in redis_conn.lrange(redis_key, 0, -1):
        p = json_decoder.decode(plan.decode())
        if not isinstance(p, str):
            sp.append(p)

    if not sp:
        logger.warning("No Plan found: {0}; no plan for the session".format(plan_url))
        raise Http404()

    try:
        plan = next(filter(lambda mp: mp['unique_url'] == plan_url, sp))
    except StopIteration:
        logger.warning("No Plan Found: {0}; there are plans for this session".format(plan_url))
        raise Http404()

    selected_addon_plans = addon_plans_from_dict(
        request.session.get('{0}-{1}-{2}'.format(quote_request_form_data['quote_store_key'],
                                                 plan['unique_url'], "addon-plans"), [])
    )
    logger.info("no of selected addon plans: {0}, for plan: {1}".format(len(selected_addon_plans), plan['unique_url']))

    addon_plans = addon_plans_from_json_data(redis_conn.lrange(
        "{0}:{1}".format(redis_key, plan['plan_name_for_img']),
        0, -1)
    )

    form = AddonPlanForm(addon_plans, selected_addon_plans, data=request.POST)
    if action == 'include' and form.is_valid() and form.add_addon_plan():
        selected_addon_plans.add(form.addon_plan)
        request.session['{0}-{1}-{2}'.format(quote_request_form_data['quote_store_key'],
                                             plan['unique_url'], "addon-plans")] = [
            addon_plan.data_as_dict() for addon_plan in selected_addon_plans
        ]
        request.session.modified = True
        remaining_addon_plans = addon_plans.difference(selected_addon_plans)

    if action == 'remove' and form.is_valid() and form.remove_addon_plan():
        selected_addon_plans.remove(form.addon_plan)
        request.session['{0}-{1}-{2}'.format(quote_request_form_data['quote_store_key'],
                                             plan['unique_url'], "addon-plans")] = [
            addon_plan.data_as_dict() for addon_plan in selected_addon_plans
        ]
        request.session.modified = True
        remaining_addon_plans = addon_plans.difference(selected_addon_plans)
    if not form.errors.items():
        return JsonResponse({
            'status': 'success',
            'action': action,
            'related_addon': form.addon_plan.data_as_dict(),
            'addon_plans': [addon_plan.data_as_dict() for addon_plan in addon_plans],
            'remaining_addon_plans': [addon_plan.data_as_dict() for addon_plan in remaining_addon_plans],
            'selected_addon_plans': [addon_plan.data_as_dict() for addon_plan in selected_addon_plans],
            'include_action': reverse('quotes:stm_plan_addon_action', args=[plan_url, 'include']),
            'remove_action': reverse('quotes:stm_plan_addon_action', args=[plan_url, 'remove'])
        })
    logger.warning("stm_plan_addon_action form error: {0}".format(dict(form.errors.items())))
    return JsonResponse({
        "status": 'failed',
        "action": action,
        'related_addon': form.addon_plan.data_as_dict() if form.addon_plan else {"Name": "Unknown"},
        "errors": dict(form.errors.items()),
        "error_keys": list(form.errors.keys()),
    })


def stm_application(request, plan_url) -> HttpResponseRedirect:
    """ Shows you the plan+addons selected and sends you to enrollment stage 1.

    :param request: Django request object
    :param plan_url: url created by joining app_url and vimm_enroll_id
    :return: HttpResponseRedirect
    """
    logger.info("starting application for plan: {0}".format(plan_url))
    request.session['applicant_enrolled'] = False
    request.session.modified = True
    quote_request_form_data = request.session.get('quote_request_form_data', {})
    if quote_request_form_data and form_data_is_valid(quote_request_form_data) == False:
        quote_request_form_data = {}
        request.session['quote_request_form_data'] = {}
        request.session['quote_request_formset_data'] = []
    sp = []
    if quote_request_form_data:
        redis_key = "{0}:{1}".format(request.session._get_session_key(),
                                     quote_request_form_data['quote_store_key'])
        for plan in redis_conn.lrange(redis_key, 0, -1):
            p = json_decoder.decode(plan.decode())
            if not isinstance(p, str):
                sp.append(p)
    if not quote_request_form_data or not sp:
        return HttpResponseRedirect(reverse('quotes:plans', args=[]))

    try:
        plan = next(filter(lambda mp: mp['unique_url'] == plan_url, sp))
    except StopIteration:
        logger.warning("Starting application failed. No Plan Found:"
                       " {0}; there are plans for this session".format(plan_url))
        raise Http404()

    plan = copy.deepcopy(plan)
    selected_addon_plans = copy.deepcopy(addon_plans_from_dict(
        request.session.get(
            '{0}-{1}-{2}'.format(quote_request_form_data['quote_store_key'], plan['unique_url'], "addon-plans"), [])
    ))

    session_vimm_enroll_id = request.session.get(f'{plan_url}_vimm_enroll_id')
    if session_vimm_enroll_id is None:
        plan['vimm_enroll_id'] = get_random_string()
    else:
        plan['vimm_enroll_id'] = session_vimm_enroll_id

    application_url = "{0}-{1}".format(plan['unique_url'], plan['vimm_enroll_id'])
    logger.info("app url: {0}".format(application_url))

    # Updating vimm enroll id of leads
    update_lead_vimm_enroll_id(qm.Leads, quote_request_form_data['quote_store_key'], plan['vimm_enroll_id'])

    stm_enroll_obj = save_to_db(
        plan=plan,
        application_url=application_url,
        form_data=quote_request_form_data,
        has_dependents=has_dependents(quote_request_form_data)
    )

    addon_plans: List[Dict] = [addon_plan.data_as_dict() for addon_plan in selected_addon_plans]

    stm_addon_plan_objs = qm.AddonPlan.objects.filter(vimm_enroll_id=plan['vimm_enroll_id'])
    if not stm_addon_plan_objs.exists() and selected_addon_plans:
        logger.info("Saving add-on plan info.")
        save_add_on_info(qm.AddonPlan, addon_plans, plan, stm_enroll_obj)
    elif stm_addon_plan_objs.exists() and selected_addon_plans:
        logger.info(f'Deleting old addons from database for {session_vimm_enroll_id}.')
        stm_addon_plan_objs.delete()
        save_add_on_info(qm.AddonPlan, addon_plans, plan, stm_enroll_obj)
    elif not selected_addon_plans:
        stm_addon_plan_objs.delete()


    if not request.session.get(application_url, {}):
        request.session[application_url] = plan
        request.session["{0}_form_data".format(application_url)] = copy.deepcopy(quote_request_form_data)
        request.session["{0}-addon-plans".format(application_url)] = addon_plans

        request.session[f'{plan_url}_vimm_enroll_id'] = plan['vimm_enroll_id']
        request.session.modified = True
    return HttpResponseRedirect(reverse('quotes:stm_enroll', args=[application_url]))



def has_dependents(form_data):
    if ((form_data['Include_Spouse'] == 'Yes' or form_data['Children_Count'] > 0)
            and form_data['applicant_is_child'] == False):
        return True
    return False



def get_enroll_object(vimm_enroll_id):
    try:
        return qm.StmEnroll.objects.get(vimm_enroll_id=vimm_enroll_id)
    except ObjectDoesNotExist:
        return None


def get_plan_object(stm_enroll_obj, vimm_enroll_id):
    try:
        stm_plan_model = getattr(qm, stm_enroll_obj.stm_name.title().replace(' ', ''))
        stm_plan_obj = stm_plan_model.objects.get(vimm_enroll_id=vimm_enroll_id)
        return stm_plan_obj
    except ObjectDoesNotExist:
        return None



def save_to_db(plan: Dict,
               application_url: str,
               form_data: Dict,
               has_dependents: bool = False,) -> qm.StmEnroll.objects:

    vimm_enroll_id = plan['vimm_enroll_id']

    stm_enroll_obj = get_enroll_object(vimm_enroll_id)
    if stm_enroll_obj:
        stm_plan_obj = get_plan_object(stm_enroll_obj, vimm_enroll_id)
    else:
        stm_plan_obj = None



    if stm_enroll_obj and stm_plan_obj:
        stm_dependent_objs = qm.Dependent.objects.filter(vimm_enroll_id=vimm_enroll_id)
    else:
        stm_dependent_objs = None

    with transaction.atomic():
        logger.info("Saving to database.")
        logger.info("Creating initial stm enroll data.")

        if stm_enroll_obj is None:
            stm_enroll_obj = qm.StmEnroll(vimm_enroll_id=plan['vimm_enroll_id'],
                                          stm_name=plan['Name'],

                                          app_url=application_url,

                                          Age = form_data['Applicant_Age'],
                                          DOB = QR_DATE_PATTERN.sub(r'\3-\1-\2', form_data.get('Applicant_DOB', None)),
                                          Effective_Date = QR_DATE_PATTERN.sub(r'\3-\1-\2', form_data.get('Effective_Date', None)),
                                          Gender = form_data['Applicant_Gender'],
                                          State = form_data['State'],
                                          Tobacco = form_data['Tobacco'],
                                          ZipCode = form_data['Zip_Code'],
                                          Applicant_is_Child = form_data['applicant_is_child'],
                                          stage='1')
            stm_enroll_obj.save()

        if stm_plan_obj is None:
            logger.info("Saving Plan Info.")
            stm_plan_model = getattr(qm, plan['Name'].title().replace(' ', ''))
            stm_plan_obj = stm_plan_model(stm_enroll=stm_enroll_obj, **plan)
            stm_plan_obj.save()

        if has_dependents and stm_dependent_objs is None:
            logger.info("Creating initial dependents entry.")

            dependents = form_data.get('Dependents', None)

            if form_data['Include_Spouse']:
                qm.Dependent.objects.create(
                    stm_enroll=stm_enroll_obj,
                    Relation='Spouse',
                    Gender=form_data['Spouse_Gender'],
                    vimm_enroll_id=plan['vimm_enroll_id'],
                    DOB=QR_DATE_PATTERN.sub(r'\3-\1-\2', form_data.get('Spouse_DOB', None)),
                    Tobacco=form_data.get('Spouse_Tobacco', None),
                    Age=form_data.get('Spouse_Age', None)
                )

            for dependent in dependents:
                qm.Dependent.objects.create(
                    stm_enroll=stm_enroll_obj,
                    vimm_enroll_id=plan['vimm_enroll_id'],
                    Gender=dependent.get('Child_Gender', None),
                    Relation='Child',
                    DOB=QR_DATE_PATTERN.sub(r'\3-\1-\2', dependent.get('Child_DOB', None)),
                    Tobacco=dependent.get('Child_Tobacco', None),
                    Age=dependent.get('Child_Age', None)
                )

        return stm_enroll_obj



def stm_enroll(request, application_url, stage=None, template=None):
    """STM enroll function for enrollment of the user

    :param request: Django request object
    :param application_url: application url for the plan object
    application_url = plan_url + vimm_enroll_id
    :type application_url: str
    :returns: JsonResponse or HttpResponseRedirect object
    :rtype: Django JsonResponse object/ Django HttpResponseRedirect object

    **NOTE** In the commit 527:26b8904d543857c79714eb854c61c8d27e898786(implemented esign)
    I had changed very little in this function. The main difference is that, it was doing
    enrollment in stage 5 and now we are doing this in e_signature_verification method.
    """

    if stage is None:
        stage = 1
    else:
        stage = int(stage)

    ajax_request = False
    if request.is_ajax():
        ajax_request = True

    plan = request.session.get(application_url, {})
    vimm_enroll_id = application_url.rsplit('-', 1)[-1]

    def quote_error_html(quote_id):
        """

        :param quote_id: int, quote ID given from HIIq
        :return: html to show in case of user getting back
        after esign request.
        """
        """ We make a http response and serve it when User has already
        submitted his esign request We determine that by checking for
        esign_req_sent_{} key in the session dictionary. We collect 
        quote ID from the plan object or from the plan dictionary.

        Also in near future, we shall replace it with a html page.
        """
        # html = """<html>
        #             <body>
        #                 <h1>Already submitted from this quote. ID #{0}</h1>
        #                 <a href={1}>Click here to go to application review</a>
        #             </body>
        #        </html>""".format(quote_id, (reverse('quotes:stm_enroll', args=[plan_url, 4])))

        html = render_to_string('quotes/quote_error.html', {
            "quote_id": quote_id,
            "url": reverse('quotes:stm_enroll', args=[application_url, 4])
        })
        print(html)
        return html

    stm_enroll_obj = None
    stm_plan_obj = None
    stm_dependent_objs = None
    stm_addon_plan_objs = None
    try:
        stm_enroll_obj = qm.StmEnroll.objects.get(vimm_enroll_id=vimm_enroll_id)
        stm_plan_model = getattr(qm, 'MainPlan')
        stm_plan_obj = stm_plan_model.objects.get(vimm_enroll_id=vimm_enroll_id)
        stm_dependent_objs = qm.Dependent.objects.filter(vimm_enroll_id=vimm_enroll_id)
        stm_addon_plan_objs = qm.AddonPlan.objects.filter(vimm_enroll_id=vimm_enroll_id)
        if not plan:
            plan = stm_plan_obj.get_json_data()
    except (ObjectDoesNotExist, AttributeError) as err:
        logger.warning("getting application data from db: {0}".format(str(err)))
        pass

    try:
        if stm_enroll_obj.enrolled and not stm_enroll_obj.esign_checked_and_enrolled_by_system:
            """
            If the user is enrolled and has pressed the back button to go back, 
            we shall bring him to the home page. Also we can destroy the session 
            variables.#TODO: destroy session vars.
            """
            return HttpResponseRedirect(reverse('quotes:home'))
    except AttributeError as a:
        print("Applicant is not enrolled")

    # addon plans
    selected_addon_plans = []
    if stm_addon_plan_objs is None:
        logger.info("GETTING ADD-ON PLAN FROM SESSION")
        selected_addon_plans = request.session.get("{0}-addon-plans".format(application_url), [])
    elif stm_addon_plan_objs:
        logger.info("GETTING ADD-ON PLANS FROM DB")
        selected_addon_plans = [addon_plan.data_as_dict() for addon_plan in stm_addon_plan_objs]
    logger.info("no of selected addon plans: {0}".format(len(selected_addon_plans)))

    if not application_url and not ajax_request:
        raise Http404()
    elif not application_url:
        return JsonResponse({'status': 'failed', 'redirect_url': reverse('quotes:plans', args=[])})

    quote_request_form_data = request.session.get('{0}_form_data'.format(application_url), {})
    if quote_request_form_data and form_data_is_valid(quote_request_form_data) == False:
        quote_request_form_data = {}

    if not quote_request_form_data and not ajax_request:
        # need a fix for ajax request
        return HttpResponseRedirect(reverse('quotes:plans', args=[]))

    stm_stages = request.session.get('enroll_{0}_stm_stages'.format(application_url), None)
    if stm_stages is None:
        request.session['enroll_{0}_stm_stages'.format(application_url)] = []
        stm_stages = []
    logger.info('stm stages: {0}'.format(stm_stages))
    stage = get_app_stage(stage, stm_stages)
    logger.info("{0}: {1}".format(stage, type(stage)))
    logger.info("PLAN::::: -> {0}".format(plan))
    ctx = {'plan': plan, 'plan_url': application_url, 'form_data': quote_request_form_data,
           'stage': stage, 'selected_addon_plans': selected_addon_plans, 'stm_enroll_obj': stm_enroll_obj}

    if stage == 4 and stm_enroll_obj.esign_checked_and_enrolled_by_system and stm_enroll_obj.enrolled:
        return HttpResponseRedirect(reverse('quotes:thank_you', args=[stm_enroll_obj.vimm_enroll_id]))

    if stage < 5:
        request.session['applicant_enrolled'] = False
        request.session.modified = True
        ctx.update({'next_stage': stage + 1})

    stm_questions_key = 'enroll_{0}_stm_question'.format(application_url)
    stm_questions = request.session.get(stm_questions_key, {})

    if stage == 1 and plan['Name'] in ['Unified Health One', 'Cardinal Choice']:
        unified_health_one_question_retrieved = False
        if not stm_questions:
            stm_questions = get_stm_questions(plan['Quote_ID'], selected_addon_plans)
            unified_health_one_question_retrieved = True
        if stm_questions and unified_health_one_question_retrieved:
            for k, v in stm_questions.items():
                v['Text'] = v['Text'].replace('If yes, complete this section.', '')
                v['CorrectAnswer'] = 'Yes'
                v['user_answer'] = 'No'
                v['g_order'] = v['order']
                try:
                    del v['SubQue']
                except KeyError:
                    pass
            request.session[stm_questions_key] = stm_questions
            request.session.modified = True

    if stage == 1 and plan['Name'] in ['Principle Advantage', 'Unified Health One',
                                       'Cardinal Choice', 'Vitala Care',
                                       'Health Choice', 'Legion Limited Medical',
                                       'USA Dental', 'Foundation Dental',
                                       'Safeguard Critical Illness', 'Freedom Spirit Plus']:
        if (StageOneTransitionForm.STAGE not in
                request.session['enroll_{0}_stm_stages'.format(application_url)]):
            request.session['enroll_{0}_stm_stages'.format(application_url)].append(
                StageOneTransitionForm.STAGE
            )
            request.session.modified = True
        stage = 2

    # Application Stage One - Eligibility Questions
    if stage == 1:
        """ In the next 22 line, we are checking if the Plan object or plan exists with the 
        quote id given from the app_url/plan_url. We do this to prevent repeat registration 
        attempt. These steps are happening in both stage 2 and 3. I'll create a function and
        remove unncecessary branching. """
        if stm_plan_obj:
            if 'esign_req_sent_{0}'.format(stm_plan_obj.Quote_ID) in request.session:
                try:
                    if request.session['esign_req_sent_{0}'.format(stm_plan_obj.Quote_ID)] is True:
                        return HttpResponse(quote_error_html(stm_plan_obj.Quote_id))
                except KeyError as k:
                    print("Quote ID can be submitted -  Stage 1")
                except AttributeError as a:
                    print("Stm Object exists but quote ID does not exist")
                    if plan:  # TODO: Refractor and reduce unncecessary branching.
                        try:
                            if 'esign_req_sent_{0}'.format(plan['Quote_ID']) in request.session:
                                if request.session['esign_req_sent_{0}'.format(plan['Quote_ID'])] is True:
                                    return HttpResponse(quote_error_html(plan['Quote_ID']))
                        except KeyError as k:
                            print("Esign req not sent for this quote - STAGE 1")

                    # print("Stm Object exists... But Quote_ID does not exist... Deleting redis key")
                    # redis_conn.delete("{0}:{1}".format(request.session._get_session_key(),
                    #                                    quote_request_form_data['quote_store_key']))
                    # request.session[FEATURED_PLAN_DICT['plan_active_key']] = False
                    # return HttpResponseRedirect(reverse('quotes:plans'))

        template = 'quotes/stm_enroll_eq.html'
        logger.info("STAGE1: stm questions: {0}".format(stm_questions))
        # ajax post request
        if ajax_request and request.method == 'POST' and stm_questions:
            if request.POST.get(AppAnswerForm.REQUEST_FIELD) == AppAnswerForm.REQUEST_NAME:
                app_answer_form = AppAnswerForm(request, stm_questions_key, stm_questions, data=request.POST)
                if app_answer_form.is_valid():
                    app_answer_form.save()
                    return JsonResponse({'status': 'success', 'cleaned_data': app_answer_form.cleaned_data})
                else:
                    logger.error("STAGE1: AppAnswerForm errors - {0}".format(app_answer_form.errors))
                    return JsonResponse({'status': 'failed', 'redirect_url': reverse('quotes:plans', args=[])})
            if request.POST.get(AppAnswerCheckForm.REQUEST_FIELD) == AppAnswerCheckForm.REQUEST_NAME:
                app_answer_check_form = AppAnswerCheckForm(request, stm_questions_key, stm_questions, data=request.POST)
                if app_answer_check_form.is_valid():
                    return JsonResponse({'status': 'success', 'cleaned_data': app_answer_check_form.cleaned_data})
                else:
                    logger.error("STAGE1: AppAnswerCheckForm errors - {0}".format(app_answer_check_form.errors))
                    return JsonResponse({'status': 'failed', 'redirect_url': reverse('quotes:plans', args=[])})
            if request.POST.get(StageOneTransitionForm.REQUEST_FIELD) == StageOneTransitionForm.REQUEST_NAME:
                state_one_transition_form = StageOneTransitionForm(request, stm_questions_key,
                                                                   stm_questions, data=request.POST)
                if state_one_transition_form.is_valid():
                    if (StageOneTransitionForm.STAGE not in
                            request.session['enroll_{0}_stm_stages'.format(application_url)]):
                        request.session['enroll_{0}_stm_stages'.format(application_url)].append(
                            StageOneTransitionForm.STAGE
                        )
                        request.session.modified = True
                    return JsonResponse(
                        {'redirect_url': reverse('quotes:stm_enroll',
                                                 args=[application_url, StageOneTransitionForm.NEXT_STAGE])}
                    )
                else:
                    return JsonResponse(
                        {'redirect_url': reverse('quotes:stm_enroll',
                                                 args=[application_url, StageOneTransitionForm.STAGE])}
                    )
        elif ajax_request:
            return JsonResponse({'status': 'failed', 'redirect_url': reverse('quotes:plans', args=[])})
        # get request from browser
        if not stm_questions:
            logger.info("STAGE1: application started with question retrieval from hiiquote api")
            stm_questions = get_stm_questions(plan['Quote_ID'], selected_addon_plans)
            logger.info("STAGE1: retrieve questions - {0}".format(stm_questions))
            request.session['enroll_{0}_stm_question'.format(application_url)] = stm_questions

        stm_questions_values = sorted(stm_questions.values(), key=lambda x: x['order'])
        ctx.update({'stm_questions': get_askable_questions(stm_questions_values)})

        request.session['ongoing_session_plan_url'] = application_url
        request.session['ongoing_session_stage'] = stage

    # Application Stage Two - Personal Info
    # if applicant is child required parent info no spouse or child
    # if applicant is adult no parent info but spouse info and child info could present
    if stage == 2:
        print("Plan dictionary: ", json.dumps(plan, indent=4, sort_keys=True))
        logger.info('STAGE2: form_data - {0}'.format(quote_request_form_data))
        if stm_plan_obj:
            try:
                if 'esign_req_sent_{0}'.format(stm_plan_obj.Quote_ID) in request.session:
                    if request.session['esign_req_sent_{0}'.format(stm_plan_obj.Quote_ID)] is True:
                        return HttpResponse(quote_error_html(stm_plan_obj.Quote_ID))
            except KeyError as k:
                print("Esign req not sent for this quote - STAGE 2")
        elif plan:  # TODO: Refractor and reduce unncecessary branching.
            try:
                if 'esign_req_sent_{0}'.format(plan['Quote_ID']) in request.session:
                    if request.session['esign_req_sent_{0}'.format(plan['Quote_ID'])] is True:
                        return HttpResponse(quote_error_html(plan['Quote_ID']))
            except KeyError as k:
                print("Esign req not sent for this quote - STAGE 2")
        template = 'quotes/stm_enroll_info.html'
        has_parent = False
        has_dependents = False
        applicant_parent_info = {}
        applicant_dependents_info = {}
        if quote_request_form_data['applicant_is_child']:
            applicant_parent_info = request.session.get("applicant_parent_info_{0}".format(application_url), {})
            has_parent = True
        if ((quote_request_form_data['Include_Spouse'] == 'Yes' or quote_request_form_data['Children_Count'] > 0) and
                not quote_request_form_data['applicant_is_child']):
            has_dependents = True
            applicant_dependents_info = request.session.get(
                'applicant_dependent_info_{0}'.format(application_url), {})
        applicant_info = request.session.get('applicant_info_{0}'.format(application_url), {})
        # ajax request with form data
        if ajax_request and request.method == 'POST':
            stage_2_errors = {}
            app_form = STApplicantInfoForm(initial_form_data=quote_request_form_data,
                                           plan=plan, request=request, data=request.POST)
            if app_form.is_valid():
                request.session['applicant_info_{0}'.format(application_url)] = app_form.cleaned_data
                applicant_cleaned_data = app_form.cleaned_data
            else:
                logger.error("STAGE2: STApplicantInfoForm errors - {0}".format(app_form.errors))
                applicant_cleaned_data = {}
                stage_2_errors.update({"applicant_errors": dict(app_form.errors.items()),
                                       "applicant_error_keys": list(app_form.errors.keys())})

            parent_form = None
            applicant_parent_form_cleaned_data = None
            if has_parent:
                parent_form = STParentInfo(initial=applicant_cleaned_data, data=request.POST)
                if parent_form.is_valid():
                    applicant_parent_form_cleaned_data = parent_form.cleaned_data
                    request.session["applicant_parent_info_{0}".format(application_url)] = parent_form.cleaned_data
                else:
                    stage_2_errors.update({'parent_errors': dict(parent_form.errors.items()),
                                           'parent_error_keys': list(parent_form.errors.keys())})
            dependent_info_form_data = None
            if has_dependents:
                dependents_initial = get_initials_for_dependents_formset(quote_request_form_data)
                for item in dependents_initial:
                    item.update({'SSN': applicant_cleaned_data.get('SOC', '')})
                st_dependent_info_formset = STDependentInfoFormSet(
                    initial=dependents_initial,
                    data=request.POST,
                    form_kwargs={'plan': plan}
                )
                if st_dependent_info_formset.is_valid():
                    request.session[
                        'applicant_dependent_info_{0}'.format(application_url)
                    ] = st_dependent_info_formset.cleaned_data
                    dependent_info_form_data = st_dependent_info_formset.cleaned_data
                    logger.info("STAGE2: STDependentInfoFormSet - {0}".format(st_dependent_info_formset.cleaned_data))
                else:
                    logger.error("STAGE2: STDependentInfoFormSet errors - {0}".format(st_dependent_info_formset.errors))
                    stage_2_errors['dependent_formset_errors'] = st_dependent_info_formset.errors

            if stage_2_errors:
                stage_2_errors.update({'status': 'fail'})
                print('stage_2_errors: {0}'.format(stage_2_errors))
                return JsonResponse(stage_2_errors)
            if 2 not in request.session['enroll_{0}_stm_stages'.format(application_url)]:
                request.session['enroll_{0}_stm_stages'.format(application_url)].append(2)
                request.session.modified = True

            '''
            I have moved the time to save data from the end of stage 3 to here, the end of stage 2.
            when ajax_request is false and we save the data. 
            '''

            if request.session[application_url].get('vimm_enroll_id') is None:
                request.session[application_url]['vimm_enroll_id'] = get_random_string()
                request.session.modified = True
            # saving info to db
            with transaction.atomic():
                if stm_enroll_obj:
                    logger.info("Updating applicant info.")
                    update_applicant_info(stm_enroll_obj, applicant_cleaned_data,
                                          applicant_parent_form_cleaned_data, plan)
                    update_application_stage(stm_enroll_obj, stage)
                if stm_enroll_obj is None:
                    logger.info("Saving applicant info.")
                    stm_enroll_obj = save_applicant_info(qm.StmEnroll, applicant_cleaned_data,
                                                         applicant_parent_form_cleaned_data, plan, application_url)
                    update_application_stage(stm_enroll_obj, stage)
                if stm_plan_obj is None:
                    logger.info("Saving Plan Info.")
                    save_stm_plan(qm, plan, stm_enroll_obj)
                if stm_dependent_objs is None and has_dependents:
                    logger.info("Saving dependents Info.")
                    save_dependent_info(qm.Dependent, dependent_info_form_data, plan, stm_enroll_obj)
                if stm_dependent_objs and has_dependents:
                    logger.info("Updating dependents Info.")
                    update_dependent_info(stm_dependent_objs, dependent_info_form_data)
                if stm_addon_plan_objs is None and selected_addon_plans:
                    logger.info("Saving add-on plan info.")
                    save_add_on_info(qm.AddonPlan, selected_addon_plans, plan, stm_enroll_obj)

                try:
                    # Updating lead info in database
                    update_leads_stm_id(qm.Leads, stm_enroll_obj, quote_request_form_data['quote_store_key'])
                except (ValueError, KeyError):
                    logger.warning("Cannot update Lead info database")

            return JsonResponse(
                {'status': 'success', 'redirect_url': reverse('quotes:stm_enroll', args=[application_url, 3])}
            )
        if applicant_info:
            st_application_info_form = STApplicantInfoForm(initial_form_data=quote_request_form_data,
                                                           plan=plan, request=request, initial=applicant_info)
        else:
            st_application_info_form = STApplicantInfoForm(initial_form_data=quote_request_form_data,
                                                           plan=plan, request=request, initialize_form=True)
        parent_info_form = None
        if has_parent and applicant_parent_info:
            parent_info_form = STParentInfo(initial=applicant_parent_info)
        elif has_parent:
            parent_info_form = STParentInfo(initial=applicant_parent_info)
        st_dependent_info_formset = None
        if has_dependents and applicant_dependents_info:
            st_dependent_info_formset = STDependentInfoFormSet(initial=applicant_dependents_info)
        elif has_dependents:
            st_dependent_info_formset = get_st_dependent_info_formset(STDependentInfoFormSet, quote_request_form_data)

        request.session['ongoing_session_plan_url'] = application_url
        request.session['ongoing_session_stage'] = stage

        ctx.update({'st_application_info_form': st_application_info_form,
                    'st_dependent_info_formset': st_dependent_info_formset,
                    'parent_info_form': parent_info_form})

    if stage == 3:
        '''
        The application comes here two times in the whole process.

        First, when the user clicks "Continue to Step 3 - Payment & Billing", then it first
        goes to stage-2 and the JsonResponse sends it to stage 3. It comes here and ajax_request is False.   

        Secondly it comes here when the user clicks "Continue to Step 4 - Review". Here ajax_request is 
        true.                  
        '''
        if stm_plan_obj:
            if 'esign_req_sent_{0}'.format(stm_plan_obj.Quote_ID) in request.session:
                try:
                    if request.session['esign_req_sent_{0}'.format(stm_plan_obj.Quote_ID)] is True:
                        return HttpResponse(quote_error_html(stm_plan_obj.Quote_ID))
                except KeyError as k:
                    print("Esign req not sent for this quote. Stage - 3")
        elif plan:  # TODO: Refractor and reduce unnessary branching.
            try:
                if 'esign_req_sent_{0}'.format(plan['Quote_ID']) in request.session:
                    if request.session['esign_req_sent_{0}'.format(plan['Quote_ID'])] is True:
                        return HttpResponse(quote_error_html(plan['Quote_ID']))
            except KeyError as k:
                print("Esign req not sent for this quote - STAGE 2")

        template = 'quotes/stm_enroll_payment.html'

        applicant_info = request.session.get('applicant_info_{0}'.format(application_url), {})
        payment_info = request.session.get('payment_info_{0}'.format(application_url), {})
        if ajax_request and request.method == 'POST' and applicant_info:
            payment_method_form = PaymentMethodForm(applicant_info, data=request.POST)
            if payment_method_form.is_valid():
                request.session['payment_info_{0}'.format(application_url)] = payment_method_form.cleaned_data
                payment_info = request.session.get('payment_info_{0}'.format(application_url), {})
                if 3 not in request.session['enroll_{0}_stm_stages'.format(application_url)]:
                    request.session['enroll_{0}_stm_stages'.format(application_url)].append(3)
                    request.session.modified = True
                if stm_enroll_obj is not None and payment_info:
                    logger.info("Saving payment info.")
                    save_applicant_payment_info(stm_enroll_obj, request, application_url)
                return JsonResponse({'status': 'success',
                                     'redirect_url': reverse('quotes:stm_enroll', args=[application_url, 4])})
            else:
                logger.error("STAGE3: PaymentMethodForm errors {0}".format(payment_method_form.errors))
                return JsonResponse({'status': 'error', "errors": dict(payment_method_form.errors.items()),
                                     "error_keys": list(payment_method_form.errors.keys())})
        elif ajax_request:
            return JsonResponse({'status': 'fail',
                                 'redirect_url': reverse('quotes:stm_enroll', args=[application_url, 2])})
        if not applicant_info:
            return HttpResponseRedirect(reverse('quotes:stm_enroll', args=[application_url, 3]))
        if payment_info:
            payment_method_form = PaymentMethodForm(applicant_info, initial=payment_info)
        else:
            payment_method_form = PaymentMethodForm(applicant_info, initialize_form=True)

        request.session['ongoing_session_plan_url'] = application_url
        request.session['ongoing_session_stage'] = stage

        ctx.update({'payment_method_form': payment_method_form, 'applicant_info': applicant_info})

    if stage == 4:
        template = 'quotes/stm_enroll_review.html'
        if ajax_request and request.method == 'POST':

            if stm_enroll_obj.esign_checked_and_enrolled_by_system and stm_enroll_obj.enrolled:
                return HttpResponseRedirect(reverse('quotes:thank_you', args=[stm_enroll_obj.vimm_enroll_id]))

            enrolled_form = GetEnrolledForm(request.POST)
            if enrolled_form.is_valid():
                if 4 not in request.session['enroll_{0}_stm_stages'.format(application_url)]:
                    request.session['enroll_{0}_stm_stages'.format(application_url)].append(4)
                    request.session.modified = True
                return JsonResponse({'status': 'success',
                                     'redirect_url': reverse('quotes:stm_enroll', args=[application_url, 5])})
            else:
                return JsonResponse({'status': 'fail', 'error_msg': 'provide consent'})
        applicant_info = request.session.get('applicant_info_{0}'.format(application_url), {})
        payment_info = request.session.get('payment_info_{0}'.format(application_url), {})
        stm_questions = request.session.get('enroll_{0}_stm_question'.format(application_url), {})
        stm_questions_values = sorted(stm_questions.values(), key=lambda x: x['order'])
        applicant_parent_info = request.session.get("applicant_parent_info_{0}".format(application_url), {})
        applicant_dependents_info = request.session.get('applicant_dependent_info_{0}'.format(application_url), {})
        logger.info("STAGE4: applicant = {0}".format(applicant_info))
        logger.info("STAGE4: parent = {0}".format(applicant_parent_info))
        logger.info("STAGE4: payment = {0}".format(payment_info))
        logger.info("STAGE4: question = {0}".format(stm_questions_values))
        logger.info("STAGE4: dependents = {0}".format(applicant_dependents_info))
        logger.info("STAGE4: {0}".format(plan))

        esign_req_sent = False
        update_application_stage(stm_enroll_obj, stage)
        if stm_enroll_obj.esign_verification_applicant_info:
            # 23-10-18 : Create a if condition
            # Or do this altogether in e_signature_enrollment method
            # What should be done? -ds87
            if stm_enroll_obj.esign_verification_pending:
                esign_req_sent = True
                request.session['esign_req_sent_{0}'.format(stm_plan_obj.Quote_ID)] = True

        request.session['ongoing_session_plan_url'] = application_url
        request.session['ongoing_session_stage'] = stage

        ctx.update({'applicant_info': applicant_info, 'payment_info': payment_info, 'esign_req_sent': esign_req_sent})

    # Post - enrollment stage
    if stage == 5:
        template = 'quotes/stm_enroll_done.html'
        res = request.session.get('enrolled_plan_{0}'.format(application_url), '')
        formatted_enroll_response = res  # and EnrollResponse(res)
        if not res:
            applicant_info = request.session.get('applicant_info_{0}'.format(application_url), {})
            payment_info = request.session.get('payment_info_{0}'.format(application_url), {})
            stm_questions = request.session.get('enroll_{0}_stm_question'.format(application_url), {})
            stm_questions_values = sorted(stm_questions.values(), key=lambda x: x['order'])
            applicant_parent_info = request.session.get("applicant_parent_info_{0}".format(application_url), {})
            applicant_dependents_info = request.session.get('applicant_dependent_info_{0}'.format(application_url), {})
            # enr = Enroll({'Plan_ID': plan['Plan_ID'], 'Name': plan['Name']},
            #              applicant_data=applicant_info,
            #              payment_data=payment_info,
            #              question_data=stm_questions_values,
            #              parent_data=applicant_parent_info,
            #              dependents_data=applicant_dependents_info,
            #              add_on_plans_data=selected_addon_plans)
            #
            # logger.info("Enroll xml: {0}".format(enr.toXML()))
            # res = enr.get_response()
            # request.session['enrolled_plan_{0}'.format(plan_url)] = res

            if formatted_enroll_response.applicant:
                print("STAGE5: applicant info - {0}".format(formatted_enroll_response.applicant))
                logger.info("STAGE5: applicant info - {0}".format(formatted_enroll_response.applicant))
                request.session['applicant_enrolled'] = {'plan_url': application_url}
                save_enrolled_applicant_info(stm_enroll_obj, formatted_enroll_response.applicant)
                # sending mail on successful enrollment
                # send_enroll_email(request, quote_request_form_data, formatted_enroll_response, stm_enroll_obj)
                # send_sales_notification(request, stm_enroll_obj)
                # removing plans from redis after successful enrollment
                redis_conn.delete("{0}:{1}".format(request.session._get_session_key(),
                                                   quote_request_form_data['quote_store_key']))
                return HttpResponseRedirect(reverse('quotes:thank_you', args=[stm_enroll_obj.vimm_enroll_id]))
            else:
                print("STAGE5: enrollment error - {0}".format(formatted_enroll_response.error))
                logger.warning("STAGE5: enrollment error - {0}".format(formatted_enroll_response.error))
                # if PREVIOUSLY_ENROLLED_ERROR_TEXT in str(formatted_enroll_response.error):
                # removing plans from redis after failed enrollment - previously enrolled
                redis_conn.delete("{0}:{1}".format(request.session._get_session_key(),
                                                   quote_request_form_data['quote_store_key']))
        else:
            return HttpResponseRedirect(reverse('quotes:thank_you', args=[stm_enroll_obj.vimm_enroll_id]))

        ctx.update({'res': formatted_enroll_response})
    return render(request, template, ctx)


def get_plan_quote_data_ajax(request: WSGIRequest) -> Union[JsonResponse, HttpResponseRedirect]:
    """This page is called from the plan_list_lim.html the first time the page
    is loaded. This function returns the plans.

    :param request: Django HttpRequest
    :return: JsonResponse
    """
    print(f'Calling AJAX. Time: {datetime.now().strftime("%H:%M:%S")}')

    quote_request_form_data = request.session.get('quote_request_form_data', {})
    ins_type = quote_request_form_data.get('Ins_Type', None)

    preference = request.session.get('quote_request_preference_data', {})
    request.session.modified = True

    plan_list = []

    redis_key = get_redis_key(request, ins_type)

    if not quote_request_form_data or not redis_conn.exists(redis_key):
        plan_list = ['START', 'END']
        return JsonResponse({
        'monthly_plans': plan_list # TODO: Properly handle error
    })


    for pdx, matched_plan in enumerate(redis_conn.lrange(redis_key, 0, -1)):
        decoded_plan = json_decoder.decode(matched_plan.decode())

        if decoded_plan == 'START':
            pass

        elif decoded_plan == 'END':
            carrier_list = set(x['Name'] for x in plan_list[1:-1])

            for carrier_name in carrier_list:
                featured_plan = get_featured_plan(carrier_name, plan_list, ins_type)
                if featured_plan:
                    featured_plan['featured_plan'] = True
                    plan_list[plan_list.index(featured_plan)] = featured_plan
                else:
                    print(f'Featured plan not found for {carrier_name}')

        elif ins_type == 'stm' and decoded_plan['Name'] in [*preference]:
            if (
                    decoded_plan['Duration_Coverage'] not in preference[decoded_plan['Name']]['Duration_Coverage'] or
                    decoded_plan['Coverage_Max'] not in preference[decoded_plan['Name']]['Coverage_Max'] or
                    decoded_plan['Coinsurance_Percentage'] not in preference[decoded_plan['Name']]['Coinsurance_Percentage'] or
                    decoded_plan['Benefit_Amount'] not in preference[decoded_plan['Name']]['Benefit_Amount']
            ):
                continue

        plan_list.append(decoded_plan)


    return JsonResponse({
        'monthly_plans': plan_list,
    })


def is_ins_type_valid(ins_type) -> bool:
    if ins_type in ['stm', 'lim', 'anc']:
        return True
    return False



def get_redis_key(request: WSGIRequest, ins_type: str) -> str:
    quote_request_form_data = request.session.get('quote_request_form_data', {})
    quote_store_key = quote_request_form_data['quote_store_key']


    if is_ins_type_valid(ins_type):
        quote_store_key = quote_store_key[:-3] + ins_type


    redis_key = "{0}:{1}".format(request.session._get_session_key(), quote_store_key)

    return redis_key





def get_featured_plan(carrier_name, plan_list, ins_type):
    """

    :return:
    """

    plans = None

    try:
        featured_plan_attr = settings.FEATURED_PLAN_DICT[carrier_name]
        premium = settings.FEATURED_PLAN_PREMIUM_DICT[ins_type]
    except KeyError:
        print(f'Featured plan attribute not found for {carrier_name}')
        return

    eligible_plans = list(filter(lambda  x: float(x['Premium']) > premium and
                                                  x['Name'] == carrier_name, plan_list[1:-1]))

    if len(eligible_plans) == 0:
        eligible_plans = plan_list[1:-1]

    for attr in featured_plan_attr:
        plans = list(filter(lambda mp: mp[attr] == featured_plan_attr[attr], eligible_plans))
        if len (plans) > 0:
            eligible_plans = plans
        else:
            return eligible_plans[0]


    if plans:
        return plans[0]


def e_signature_enrollment(request, vimm_enroll_id):
    """E Signature Enrollment function for customer signature.

    :param request: Django request object
    :param vimm_enroll_id: random string, unique field in Enroll object
    :return: Django JsonResponse object

    In the enrollment review page(stage 4) when the user clicks the button for esign,
    this method is called by AJAX. We get the STM enrollment object using the vimm_enroll_id.

    There is a test case when user has already enrolled but somehow has gotten to this page
    and pressed the esign req button. We'll prevent him from again resubmitting
    by sending him to Thank You page.

    Bear in mind, we are putting a session variable called esign_req_sent in request.session.
    When it is true, this button will not show up.

    When the user reaches the end of the function we'll delete the redis key.
    We are also deleting the key in stage 5 which might be unnecessary.

    Some features like post_date, logger will be implemented. -ds87

    """
    if request.is_ajax() and request.POST:
        enrolled_form = GetEnrolledForm(request.POST)
        if not enrolled_form.is_valid():
            return JsonResponse({'status': 'fail', 'error_msg': 'provide consent'})

    # request_user_info = log_user_info(request.user)
    logger.info('Starting E-Signature enrollment...log_vimm_enroll_id: {0}'.format(vimm_enroll_id))
    stm_enroll_obj = None
    stm_dependent_objs = []
    # hii_addon_plan_objs = []
    # a1_addon_plan_objs = []
    main_plan_obj = None
    # carrier = None
    try:
        # stm_enroll_obj = qm.StmEnroll.objects.get(vimm_enroll_id=vimm_enroll_id, discarded=False, enrolled=False)
        stm_enroll_obj = qm.StmEnroll.objects.get(vimm_enroll_id=vimm_enroll_id, enrolled=False)
        stm_dependent_objs = stm_enroll_obj.dependent_set.all()
        # hii_addon_plan_objs = stm_enroll_obj.addonplan_set.filter(Q(api_source='hii'))
        hii_addon_plan_objs = stm_enroll_obj.addonplan_set.all()
        # a1_addon_plan_objs = stm_enroll_obj.addonplan_set.filter(Q(api_source='a1'))
        main_plan_obj = stm_enroll_obj.get_stm_plan()
        # main_plan_obj = stm_enroll_obj.
        # carrier = Carrier.objects.get(name=stm_enroll_obj.stm_name)
    except ObjectDoesNotExist as err:
        logger.debug('Object does not exist on StmEnroll table\n vimm_enroll_id: {0}'.format(vimm_enroll_id))
        logger.error("Error on esign enrollment: {0} \nvimm_enroll_id: {1}".format(err, vimm_enroll_id))
        print("Stm enroll object does not exist or it is enrolled.")
        try:
            stm_enroll_obj = qm.StmEnroll.objects.get(vimm_enroll_id=vimm_enroll_id, enrolled=True)
            print("STM enroll object exists and is enrolled")

            # Is this risky? we may send login url to the wrong person. Whats the alternative? -ds87
            request.session['applicant_enrolled'] = {'plan_url': stm_enroll_obj.app_url}
            return JsonResponse(
                {'status': 'success', 'redirect_url': reverse('quotes:thank_you', args=[stm_enroll_obj.vimm_enroll_id])})

        except ObjectDoesNotExist as err:
            print("STM enroll object does not exist confirmed.")

    # finally:
    #     # This is useless and should be deleted
    #     if stm_enroll_obj and stm_enroll_obj.enrolled:
    #         logger.warning('already enrolled')
    #         return JsonResponse({
    #             'status': 'failed',
    #             'redirect_url': reverse('ins_supervisor:details_of_stm_enroll',
    #                                     args=[stm_enroll_obj.vimm_enroll_id])
    #         })

    # if not main_plan_obj or not carrier:
    #     logger.error("not stm_plan_obj or not carrier")
    #     raise Http404()

    application_url = stm_enroll_obj.app_url

    hii_formatted_enroll_response = None

    if stm_enroll_obj.esign_verification_starts and stm_enroll_obj.esign_verification_pending:
        res = json_decoder.decode(stm_enroll_obj.esign_verification_applicant_info or '{}')
        hii_formatted_enroll_response = res and EnrollResponse(res)
        # hii_formatted_enroll_response = res and EnrollResponse(res, request=request_user_info)

    if hii_formatted_enroll_response:
        print(hii_formatted_enroll_response)
        return JsonResponse({
            'status': 'success',
            'res': hii_formatted_enroll_response.applicant,
            'verification': 'Y'
        })

    # TODO: Need to put quote_request_form_data in model
    # quote_request_form_data = json_decoder.decode(stm_enroll_obj.form_data)

    quote_request_form_data = request.session.get('{0}_form_data'.format(stm_enroll_obj.app_url), {})
    if quote_request_form_data and not form_data_is_valid(quote_request_form_data):
        quote_request_form_data = {}
    if not quote_request_form_data:
        logger.warning('quote_request_form_data - empty')
        return JsonResponse({
            'status': 'failed',
            'redirect_url': reverse('ins_supervisor:verify_and_enroll', args=[stm_enroll_obj.vimm_enroll_id])
        })

    stage = int(stm_enroll_obj.stage or 1)
    stm_stages = request.session.get('enroll_{0}_stm_stages'.format(application_url), None)
    if stm_stages is None:
        request.session['enroll_{0}_stm_stages'.format(application_url)] = []
        stm_stages = []
    stage = get_app_stage(stage, stm_stages)
    if stage != 4:
        return JsonResponse({
            'status': 'failed',
            'error_message': 'Refresh the page & try again.'
        })

    # if not post_date_test(stm_enroll_obj, Carrier):
    #     return JsonResponse({
    #         'status': 'failed',
    #         'error_message': 'ESignature verification is not allowed.'
    #     })

    final_response = {
        'status': 'error',
        'verification': 'Y',
        'api_source': 'hii',
        'cross_enrollment': False
    }

    esign_verification_update_fields = []

    plan = main_plan_obj.get_json_data()
    selected_addon_plans = [addon_plan.data_as_dict() for addon_plan in hii_addon_plan_objs]
    # TODO: Populate applicant info
    # applicant_info = stm_enroll_obj.get_applicant_info_for_update()

    # payment_info = stm_enroll_obj.get_billing_payment_info()
    # stm_questions = json_decoder.decode(stm_enroll_obj.question_data or '{}')

    # Question: Why do we do this? -ds87
    applicant_info = request.session.get('applicant_info_{0}'.format(application_url), {})
    applicant_info = copy.deepcopy(applicant_info)

    applicant_info.update({
        'ESign_Option': settings.ESIGNATURE_VERIFICATION,
        'Esign_Option': settings.ESIGNATURE_VERIFICATION,
        'ESign_Send_Method': settings.ESIGN_SEND_METHOD,
    })
    # stm_questions_values = sorted(stm_questions.values(), key=lambda x: x['order'])

    res = request.session.get('enrolled_plan_{0}'.format(application_url), '')
    print(f'applicant_info: {json.dumps(applicant_info, indent=4, sort_keys=True)}')
    if not res:
        # applicant_info = applicant_info
        payment_info = request.session.get('payment_info_{0}'.format(application_url), {})
        applicant_parent_info = stm_enroll_obj.get_applicant_parent_info()
        applicant_dependents_info = [dependent.get_json_data() for dependent in stm_dependent_objs]
        stm_questions = request.session.get('enroll_{0}_stm_question'.format(application_url), {})
        stm_questions_values = sorted(stm_questions.values(), key=lambda x: x['order'])
        enr = Enroll({'Plan_ID': plan['Plan_ID'], 'Name': plan['Name']},
                     applicant_data=applicant_info,
                     payment_data=payment_info,
                     question_data=stm_questions_values,
                     parent_data=applicant_parent_info,
                     dependents_data=applicant_dependents_info,
                     add_on_plans_data=selected_addon_plans)

    # TODO: Implement post date
    # if stm_enroll_obj.is_post_date and has_post_date_api(stm_enroll_obj, Carrier):
    #     post_date = stm_enroll_obj.post_date
    #     delay_application_date = post_date.strftime('%Y-%m-%d')
    #     applicant_info.update({
    #         'Delay_Application_Flag': 'Y',
    #         'Delay_Application_Date': stm_enroll_obj.post_date.strftime('%Y-%m-%d')
    #     })

    res = enr.get_response()
    logger.info('Esign Verification applicant info:\nResponse: {0}\nlog_vimm_enroll_id: {1}'.format(res, vimm_enroll_id))
    print('\n\nenrolled response: ', res)
    stm_enroll_obj.esign_verification_applicant_info = json_encoder.encode(res)
    stm_enroll_obj.save(update_fields=['esign_verification_applicant_info'])
    print(esign_verification_update_fields)
    res2_formatted = None
    # TODO Post date
    # if stm_enroll_obj.is_post_date:
    #     try:
    #         res1 = res.split('</Result>', 1)[0] + '</Result>'
    #         res2 = res.split('</Result>', 1)[1]
    #         logger.info("Esign Verification post date res2: {0}".format(res2),
    #                     user_info=request_user_info, log_vimm_enroll_id=vimm_enroll_id)
    #         if res2.strip():
    #             try:
    #                 res2_formatted = ESignResponse(res2, request=request_user_info)
    #             except ParseError as err:
    #                 logger.warning("Esign Verification res2 parse error: {0}".format(err),
    #                                user_info=request_user_info, log_vimm_enroll_id=vimm_enroll_id)
    #                 res1 = res
    #         res = res1
    #     except IndexError:
    #         pass
    hii_formatted_enroll_response = ESignResponse(res)  # , request=request_user_info)
    logger.info(hii_formatted_enroll_response)
    final_response['error'] = hii_formatted_enroll_response.error

    if hii_formatted_enroll_response.applicant:
        if res2_formatted and res2_formatted.applicant:
            hii_formatted_enroll_response.applicant.update(res2_formatted.applicant)
        logger.info("Esign Verification applicant info -- Formatted Enroll Response: {0} -- Applicant Info: {1}".format(
            hii_formatted_enroll_response.applicant,
            log_user_info(request.session.get('applicant_info_{0}'.format(stm_enroll_obj.app_url)))))
        final_response.update({
            'status': 'success',
            'hii_applicant': hii_formatted_enroll_response.applicant,
            'esign_verification_payment': reverse('quotes:esign_verification_payment', args=[vimm_enroll_id]),
            # 'esign_verification_resend': reverse('quotes:esign_verification_resend', args=[vimm_enroll_id]),
            'main_api_source': 'hii'
        })

    if not hii_formatted_enroll_response.error:
        stm_enroll_obj.esign_verification_starts = True
        stm_enroll_obj.esign_verification_pending = True
    print("packages/quotes/views.py Line No. 1740: -- esign_verification_update_fields",
          esign_verification_update_fields)
    esign_verification_update_fields.extend(['esign_verification_starts', 'esign_verification_pending'])
    print("packages/quotes/views.py Line No. 1743: -- esign_verification_update_fields",
          esign_verification_update_fields)
    stm_enroll_obj.save(update_fields=esign_verification_update_fields)
    logger.info('Esign Enrollment: sent mail, Response:{0}, user info:{1}'.format(final_response,
                                                                                  log_user_info(request.session.get(
                                                                                      'applicant_info_{0}'.format(
                                                                                          stm_enroll_obj.app_url)))))

    # Deleting quote key
    redis_conn.delete("{0}:{1}".format(request.session._get_session_key(),
                                       quote_request_form_data['quote_store_key']))

    # Deleting vimm_enroll_id stored aginst plan_url in session
    plan_url = application_url.rsplit('-', 1)[0]
    del request.session[f'{plan_url}_vimm_enroll_id']

    return JsonResponse(final_response)


def esign_verification_payment(request, vimm_enroll_id):
    """ESign Verification for customer signature

    :param request: Django request object
    :param vimm_enroll_id: random string, unique field in Enroll object
    :returns: a object which tells ajax method to request verification for
    esignature payment.
    :rtype: Django JsonResponse object

    In the enrollment review page, if esign request has already been sent, this button
    calling this method appears.

    Clicking it gets the user data from session and asks for response from hiiquote wheather
    the user has completed his e-signature. It parses the response using functions from
    enroll.py and acts accordingly meaning it show the error if error occurs. If verification is
    a success it saves the applicant data and shows a page including the users login info.

    """
    # request_user_info = log_user_info(request.user)
    if request.is_ajax() and request.POST:
        requested_api_source = request.POST.get('api_source')
        print(requested_api_source)
    else:
        return JsonResponse({"status": "fail"})

    try:
        stm_enroll_obj = qm.StmEnroll.objects.get(
            vimm_enroll_id=vimm_enroll_id,
            enrolled=False,
            esign_verification_starts=True,
            esign_verification_pending=True
        )
    except ObjectDoesNotExist as err:
        print("stm_enroll object does not exist/Enrolled!=False")
        try:
            stm_enroll_obj = qm.StmEnroll.objects.get(
                vimm_enroll_id=vimm_enroll_id,
                enrolled=True,
                esign_verification_starts=True,
                esign_verification_pending=False
            )
            print("Object exists and is enrolled")
            request.session['applicant_enrolled'] = {'plan_url': stm_enroll_obj.app_url}

            return JsonResponse({'applicant_enrolled': True, 'redirect_url': reverse('quotes:thank_you', args=[stm_enroll_obj.vimm_enroll_id])})

        except ObjectDoesNotExist as err:
            print("stm_enroll object does not exist/Enrolled!=True")

        return JsonResponse({"status": 'fail'})

    print('\n\nHii Main plan esign check...')
    fields_to_update_on_hii_enrollment = []
    esign_res = json_decoder.decode(stm_enroll_obj.esign_verification_applicant_info or '{}')
    # applicant_info_dict = json_decoder.decode(stm_enroll_obj.applicant_info or '{}')
    applicant_info_dict = request.session.get('applicant_info_{0}'.format(stm_enroll_obj.app_url), {})
    print(applicant_info_dict)
    if not esign_res:
        return JsonResponse({'status': 'fail'})
    res2_formatted = None
    # TODO Implement post date
    # if stm_enroll_obj.is_post_date:
    #     try:
    #         res1 = esign_res.split('</Result>', 1)[0] + '</Result>'
    #         res2 = esign_res.split('</Result>', 1)[1]
    #         if res2.strip():
    #             try:
    #                 res2_formatted = ESignResponse(res2, request=request_user_info)
    #             except ParseError as err:
    #                 logger.warning("Esign Verification payment res2 parse error: {0}".format(err),
    #                                user_info=request_user_info, log_vimm_enroll_id=vimm_enroll_id)
    #                 res1 = esign_res
    #         esign_res = res1
    #     except IndexError:
    #         pass
    print(esign_res)
    formatted_esign_response = ESignResponse(esign_res)  # , request=request_user_info)
    print("formatted_esign_response.applicant:", formatted_esign_response.applicant)
    # if formatted_esign_response.applicant and res2_formatted and res2_formatted.applicant:
    #     formatted_esign_response.applicant.update(res2_formatted.applicant)

    if (not formatted_esign_response.applicant) or (not applicant_info_dict):
        return JsonResponse({'status': 'fail'})

    logger.info('formatted_esign_response.applicant: {0}, User info: {1}, enroll id:{2}'.format(
        formatted_esign_response.applicant,
        log_user_info(request.session.get('applicant_info_{0}'.format(stm_enroll_obj.app_url))),
        stm_enroll_obj.vimm_enroll_id))

    attr_data = {
        'Quote_ID': applicant_info_dict['Quote_ID'],
        'ApplicantID': formatted_esign_response.applicant['ApplicantID'],
        'Access_Token': formatted_esign_response.applicant['Access_Token'],
        'Process_Option': 'payment'
    }

    esign_enroll = ESignVerificationEnroll(attr_data=attr_data)
    try:
        res = esign_enroll.get_response()
    except requests.exceptions.RequestException as err:
        logger.error(str(err))
        return JsonResponse({'status': 'error'})

    # storing last esign checked time
    stm_enroll_obj.last_esign_checked_at = timezone.now()
    stm_enroll_obj.save(update_fields=['last_esign_checked_at'])

    hii_formatted_enroll_response = res and EnrollResponse(res)
    if hii_formatted_enroll_response.applicant:
        logger.info("ESign verified enrollment: {0}, User Information: {1}"
                    "Enrollment ID: {2}".format(hii_formatted_enroll_response.applicant,
                                                log_user_info(request.session.get(
                                                    'applicant_info_{0}'.format(stm_enroll_obj.app_url))),
                                                stm_enroll_obj.vimm_enroll_id))
        stm_enroll_obj.enrolled_plan_res = json_encoder.encode(res)
        fields_to_update_on_hii_enrollment.append('enrolled_plan_res')

        stm_enroll_obj.esign_verification_pending = False
        # TODO check and test if these two flags are working as expected.
        stm_enroll_obj.processed = True
        stm_enroll_obj.processed_at = timezone.now()
        stm_enroll_obj.esign_completed = True
        fields_to_update_on_hii_enrollment.extend(['esign_verification_pending', 'processed',
                                                   'processed_at', 'esign_completed'])
        stm_enroll_obj.save(update_fields=fields_to_update_on_hii_enrollment)
        save_enrolled_applicant_info(stm_enroll_obj, hii_formatted_enroll_response.applicant, enrolled=True)

        stm_plan_obj = qm.MainPlan.objects.get(vimm_enroll_id=vimm_enroll_id)
        stm_plan_obj.paid = True
        stm_plan_obj.save()

        # TODO: Need to implement loader from salesfusion django/templates/loader
        # enroll_info_panel_body = loader.render_to_string(
        #     'stm/render/app_stage_5_enroll_info.html',
        #     {'res': hii_formatted_enroll_response}
        # )
        """ Now doing it like before eg. stm_enroll method """
        template = 'quotes/stm_enroll_done.html'

        print("STAGE5: applicant info - {0}".format(hii_formatted_enroll_response.applicant))
        logger.info("STAGE5: applicant info - {0}".format(hii_formatted_enroll_response.applicant))
        request.session['applicant_enrolled'] = {'plan_url': stm_enroll_obj.app_url}
        save_enrolled_applicant_info(stm_enroll_obj, hii_formatted_enroll_response.applicant)
        # sending mail on successful enrollment
        # send_enroll_email(request, quote_request_form_data, formatted_enroll_response, stm_enroll_obj)
        # send_sales_notification(request, stm_enroll_obj)
        # removing plans from redis after successful enrollment

        # TODO: Put this in model
        quote_request_form_data = request.session.get('{0}_form_data'.format(stm_enroll_obj.app_url), {})
        redis_conn.delete("{0}:{1}".format(request.session._get_session_key(),
                                           quote_request_form_data['quote_store_key']))

        # Updating application stage into final stage
        update_application_stage(stm_enroll_obj, 5)

        # request.session['applicant_enrolled'] = True
        # request.session['enrolled_plan_{0}'.format(stm_enroll_obj.app_url)] = 'formatted_esign_response'
        # return HttpResponseRedirect(reverse('quotes:thank_you', args=[]))
        # return render(request, 'quotes/thank_you.html',
        #               {'plan_url': stm_enroll_obj.app_url,
        #                'form_data': quote_request_form_data,
        #                'stage': 5,
        #                'stm_enroll_obj': stm_enroll_obj})

        # print("formatting response: {}".format(formatted_esign_response))

        # enroll_info_panel_body = loader.render_to_string  (
        #     'quotes/thank_you.html',
        #     {'res': formatted_esign_response,
        #      'stm_enroll_obj': stm_enroll_obj}
        # )

        # return JsonResponse({
        #     'status': 'success',
        #     'enroll_info_panel_body': enroll_info_panel_body
        # })

        return JsonResponse(
            {'status': 'success', 'redirect_url': reverse('quotes:thank_you', args=[stm_enroll_obj.vimm_enroll_id])})


    else:
        logger.warning("ESign verification: {0}".format(hii_formatted_enroll_response.error))
        logger.info("User info: {0}".format(
            log_user_info(request.session.get('applicant_info_{0}'.format(stm_enroll_obj.app_url)))))
        print(hii_formatted_enroll_response.error)
        return JsonResponse({
            'status': "error",
            'error': hii_formatted_enroll_response.error
        })


def thank_you(request, vimm_enroll_id):
    """thank_you method for showing final information to customer.
    :param: request: Django request object.
    :returns: HttpResponse object with rendered text.
    """
    try:
        stm_enroll_obj = qm.StmEnroll.objects.get(
            vimm_enroll_id=vimm_enroll_id,
            enrolled=True,
            esign_verification_starts=True,
            esign_verification_pending=False
        )
        logger.info("Thank You page: Application found in database")

    except (ObjectDoesNotExist, AttributeError) as err:
        logger.warning("Application data not found in database: {0}.".format(str(err)))
        return HttpResponseRedirect(reverse('quotes:plan_quote', args=[]))

    # Destroying session vimm_enroll_id
    applicant_enrolled = request.session.get('applicant_enrolled', False)
    if applicant_enrolled:
        plan_url = applicant_enrolled['plan_url']
        del request.session[plan_url]['vimm_enroll_id']
        logger.info("Enroll id {0} removed from session".format(vimm_enroll_id))

    res = json_decoder.decode(stm_enroll_obj.enrolled_plan_res or '{}')
    formatted_enroll_response = res and EnrollResponse(res)
    return render(request, 'quotes/thank_you.html',
                  {'res': formatted_enroll_response})


# meta description for legal info
legal_page_info = [
    {
        'slug': 'privacy',
        'meta': 'NationsHealthInsurance.com is a full service health insurance brokerage focusing on direct to consumer relations via our revolutionary '
                'web based enrollment platform',
    },
    {
        'slug': 'terms-of-use',
        'meta': 'Terms and Conditions of Use Updated 9/10/2016',
    },
    {
        'slug': 'licensing',
        'meta': 'NationsHealthInsurance.com Licensing Information',
    },
    {
        'slug': 'copyright',
        'meta': 'NationsHealthInsurance.com respects the rights of others for their intellectual property. The following is our policy for copyright infringement notice and counter notice',
    },

]


@require_POST
def select_from_quoted_plans_ajax(request: WSGIRequest, plan_url: str) -> JsonResponse:
    """ Switch user to alternative plan containing alternate coinsurance
    percentage, coverage_max and benefit amount.

    Note: Benefit amount and max out of pocket are the same thing.
    
    """
    response = {
        'errors': [],
        'providers': []  # TODO
    }


    print(f'Fetching alternative coverage options for UNIQUE URL : {plan_url}')

    quote_request_form_data = request.session.get('quote_request_form_data', {})

    request.session['applicant_enrolled'] = False
    request.session.modified = True
    if quote_request_form_data and form_data_is_valid(quote_request_form_data) == False:
        quote_request_form_data = {}
        request.session['quote_request_form_data'] = {}
        request.session['quote_request_formset_data'] = []

    if not quote_request_form_data:
        return JsonResponse(None)

    plan_list = []
    redis_key = "{0}:{1}".format(request.session._get_session_key(),
                                 quote_request_form_data['quote_store_key'])

    print(f"redis_key: {redis_key}")

    # TODO: Set an expiration timer for plans in redis.

    for plan in redis_conn.lrange(redis_key, 0, -1):
        p = json_decoder.decode(plan.decode())
        if not isinstance(p, str):
            plan_list.append(p)

    if not plan_list:
        logger.warning("No Plan found: {0}; no plan for the session".format(plan_url))
        raise Http404()

    # We are not selecting the current plan from plan list(mp).
    try:
        plan = next(filter(lambda mp: mp['unique_url'] == plan_url, plan_list))
        stm_name = plan['Name']
    except StopIteration:
        logger.warning(f'No Plan Found: {plan_url}; there are no plan for this session')
        raise Http404()

    form = AjaxRequestAttrChangeForm(request.POST)


    coverage_duration = plan['Duration_Coverage']

    try:
        preference_for_current_stm : Optional[Dict]  = get_user_preference(request, form, plan)
        coinsurance_percentage = preference_for_current_stm['Coinsurance_Percentage']
        benefit_amount = preference_for_current_stm['Benefit_Amount']
        coverage_maximum = preference_for_current_stm['Coverage_Max']
        input_change = preference_for_current_stm['input_change']
        plan_type = preference_for_current_stm['plan_type']
    except TypeError as t:
        print(t)


    if input_change == 'Benefit_Amount':
        l = get_available_coins_against_benefit(plan_list, benefit_amount, plan)
        if coinsurance_percentage not in l:
            # coinsurance_percentage = min(l)
            preference_for_current_stm['Coinsurance_Percentage'] = coinsurance_percentage = min(l)


    elif input_change == 'Coinsurance_Percentage':
        l = get_available_benefit_against_coins(plan_list, coinsurance_percentage, plan)
        if benefit_amount not in l:
            # benefit_amount = min(l)
            preference_for_current_stm['Benefit_Amount'] = benefit_amount = min(l)


    try:
        alternative_plan = next(filter(lambda mp: mp['option'] == plan['option'] and
                                                  mp['Coinsurance_Percentage'] == coinsurance_percentage and
                                                  mp['out_of_pocket_value'] == benefit_amount and
                                                  mp['Coverage_Max'] == coverage_maximum and
                                                  mp['Duration_Coverage'] == coverage_duration and
                                                  mp['Plan'] == plan_type, plan_list))
    except StopIteration:
        logger.warning(f'No alternative plan for {plan_url}')  # We need to handle this exception in template/js
        raise Http404()

    # Alternate plan found
    alternative_plan_url = alternative_plan['unique_url']

    request.session['stm_general_url_chosen'] = True

    print(f'The ALTERNATIVE plan is {json.dumps(alternative_plan, indent=4, sort_keys=True)}')
    logger.info(f'CHANGING to alternative plan {alternative_plan_url}')
    logger.info(f'apply for plan - {alternative_plan_url}: {alternative_plan}')

    # Keeping the same addons. We might need to change this.

    selected_addon_plans = addon_plans_from_dict(
        request.session.get(
            '{0}-{1}-{2}'.format(quote_request_form_data['quote_store_key'], plan['unique_url'], "addon-plans"), [])
    )

    # Saving the currently selected addons in the session for alternative plan dictionary to avoid addon mismatch.
    request.session['{0}-{1}-{2}'.format(quote_request_form_data['quote_store_key'],
                                         alternative_plan['unique_url'], "addon-plans")] = [
        addon_plan.data_as_dict() for addon_plan in selected_addon_plans
    ]

    update_session_preferenced_data(request, stm_name, preference_for_current_stm, coverage_duration)

    logger.info(f'PLAN: {alternative_plan}')
    logger.info("ADD-ON: {0}".format([s_add_on_plan.data_as_dict() for s_add_on_plan in selected_addon_plans]))

    return JsonResponse(
        {
            'status': 'success',
            'url': reverse('quotes:stm_apply', kwargs={'plan_url': alternative_plan_url}),
            'coinsurance': alternative_plan['Coinsurance_Percentage'],
            'benefit_amount': alternative_plan['out_of_pocket_value'],
            'coverage_maximum': alternative_plan['coverage_max_value'],
            'premium': plan_actual_premium(context=None, stm_plan=alternative_plan),
            'related_plans' : get_related_plans(plan, preference_for_current_stm, plan_list),
            'plan_type': quote_request_form_data.get('Ins_Type'),
        }
    )


def update_session_preferenced_data(request: WSGIRequest,
                                    stm_name: str,
                                    preference_for_current_stm: Union[dict, None],
                                    coverage_duration: str,
                                    plan: Dict = None) -> None:
    """ Setting preference data. Note: preference has a input changed field that is unchanged. """
    quote_request_preference_data = request.session.get('quote_request_preference_data', {})

    try:
        if plan is not None:
            quote_request_preference_data[stm_name]['Coinsurance_Percentage'] = [plan['Coinsurance_Percentage']]
            quote_request_preference_data[stm_name]['Benefit_Amount'] = [plan['Benefit_Amount']]
            quote_request_preference_data[stm_name]['Coverage_Max'] = [plan['Coverage_Max']]

        elif preference_for_current_stm is not None:
            coinsurance_percentage = preference_for_current_stm['Coinsurance_Percentage']
            benefit_amount = preference_for_current_stm['Benefit_Amount']
            coverage_maximum = preference_for_current_stm['Coverage_Max']

            quote_request_preference_data[stm_name]['Coinsurance_Percentage'] = [coinsurance_percentage]
            quote_request_preference_data[stm_name]['Benefit_Amount'] = [benefit_amount]
            quote_request_preference_data[stm_name]['Coverage_Max'] = [coverage_maximum]
        quote_request_preference_data[stm_name]['Duration_Coverage'] = [coverage_duration]  # why not a dict of str Need to refractor.
    except KeyError as k:
        logger.warning(k)

    request.session['quote_request_preference_data'] = quote_request_preference_data

    return


def get_related_plans(plan, preference_dict, plan_list):
    """
    :return:
    """
    related_plans = None
    try:
        related_plans = list(filter(
            lambda mp: mp['Name'] == plan['Name'] and \
                       mp['option'] != plan['option'] and \
                       mp['Plan'] == plan['Plan'] and \
                       mp['Coinsurance_Percentage'] == preference_dict['Coinsurance_Percentage'] and \
                       mp['out_of_pocket_value'] == preference_dict['Benefit_Amount'] and \
                       mp['coverage_max_value'] == preference_dict['Coverage_Max'] and \
                       mp['Duration_Coverage'] == plan['Duration_Coverage'], plan_list))
    except KeyError as k:
        print(k)
        pass

    print("related_plans:", related_plans)
    return related_plans


def get_user_preference(request: WSGIRequest, form: AjaxRequestAttrChangeForm, plan: Dict) -> Union[Dict, None]:
    preference = {}
    if form.is_valid():
        benefit_amount = form.cleaned_data.get('Benefit_Amount', None)
        if benefit_amount == '' or None:
            benefit_amount = plan['out_of_pocket_value']
        preference['Benefit_Amount'] = benefit_amount

        coinsurance_percentage = form.cleaned_data.get('Coinsurance_Percentage', None)
        if coinsurance_percentage == '' or None:
            coinsurance_percentage = plan['Coinsurance_Percentage']
        preference['Coinsurance_Percentage'] = coinsurance_percentage

        coverage_maximum = form.cleaned_data.get('Coverage_Max', None)
        if coverage_maximum == '' or None:
            coverage_maximum = plan['Coverage_Max']
        preference['Coverage_Max'] = coverage_maximum

        plan_type = form.cleaned_data.get('Plan', None)
        if plan_type == '' or None:
            plan_type = plan['Plan']
            preference['plan_type'] = plan_type

        input_change = request.POST.get('changed', None)
        preference['input_change'] = input_change

        return preference

    else:
        return None


def alternate_duration_coverage(request: WSGIRequest, plan_url: str) -> JsonResponse:
    duration_coverage_form = DurationCoverageForm(request.POST)
    ajax_attr_form = AjaxRequestAttrChangeForm(request.POST)

    if duration_coverage_form.is_valid():
        print(f'Form is valid.')
        coverage_duration = duration_coverage_form.cleaned_data.get('Duration_Coverage', None)

        if coverage_duration is None:
            raise Http404

    if ajax_attr_form.is_valid():
        print(f'ajax_attr_form is valid.')
        changed_benefit_amount = ajax_attr_form.cleaned_data.get('Benefit_Amount', None)
        changed_coinsurance_percentage = ajax_attr_form.cleaned_data.get('Coinsurance_Percentage', None)
        changed_coverage_maximum = ajax_attr_form.cleaned_data.get('Coverage_Max', None)

        # plan_type = ajax_attr_form.cleaned_data.get('Plan', None) # Not Needed
        # input_change = request.POST.get('changed', None) # Not Needed


    print(f'Fetching alternative coverage options for UNIQUE URL : {plan_url}')

    quote_request_form_data = request.session.get('quote_request_form_data', {})
    request.session['applicant_enrolled'] = False
    request.session.modified = True
    if quote_request_form_data and form_data_is_valid(quote_request_form_data) == False:
        quote_request_form_data = {}
        request.session['quote_request_form_data'] = {}
        request.session['quote_request_formset_data'] = []

    if not quote_request_form_data:
        return HttpResponseRedirect(reverse('quotes:plans', args=[]))

    plan_list = []
    redis_key = "{0}:{1}".format(request.session._get_session_key(),
                                 quote_request_form_data['quote_store_key'])

    print(f"redis_key: {redis_key}")

    redis_done_data_flag = f'{redis_key}:done_data'
    quote_request_completed_data = json.loads(redis_conn.get(redis_done_data_flag))

    # TODO: Set an expiration timer for plans in redis.

    # Temporary hack to find out stm_name from plan_url. Will be repalced by a function later.

    if plan_url[:4].lower() == 'life':  # Lifeshield
        stm_name = 'LifeShield STM'
    else:
        stm_name = 'AdvantHealth STM'

    selection_data = create_selection_data(quote_request_completed_data, stm_name, coverage_duration)

    if not redis_conn.exists(redis_key):
        print("Redis connection does not exist for redis key")
    elif not selection_data:
        print(f'Already quoted alternative plans.')
    else:
        threaded_request(quote_request_form_data, request.session._get_session_key(), selection_data)

    for plan in redis_conn.lrange(redis_key, 0, -1):
        p = json_decoder.decode(plan.decode())
        if not isinstance(p, str):
            plan_list.append(p)

    if not plan_list:
        logger.warning("No Plan found: {0}; no plan for the session".format(plan_url))
        raise Http404()

    try:
        plan = next(filter(lambda mp: mp['unique_url'] == plan_url, plan_list))
    except StopIteration:
        logger.warning(f'No Plan Found: {plan_url}; there are no plan for this session')
        raise Http404()


    # TODO: Try catch for changed values.

    try:
        alternative_plan = next(filter(lambda mp: mp['Coinsurance_Percentage'] == changed_coinsurance_percentage and
                                                  mp['out_of_pocket_value'] == changed_benefit_amount and
                                                  mp['coverage_max_value'] == changed_coverage_maximum and
                                                  mp['Plan'] == plan['Plan'] and
                                                  mp['Duration_Coverage'] == coverage_duration, plan_list))
    except StopIteration:
        logger.warning(f'No alternative plan for {plan_url}')  # We need to handle this exception in template/js
        raise Http404()

    # Alternate plan found
    alternative_plan_general_url = alternative_plan['general_url']

    # Setting the duration coverage in preference data
    request.session['quote_request_preference_data'][stm_name]['Duration_Coverage'] = coverage_duration

    print(f'The ALTERNATIVE plan is {json.dumps(alternative_plan, indent=4, sort_keys=True)}')
    logger.info(f'CHANGING to alternative plan {alternative_plan_general_url}')
    logger.info(f'apply for plan - {alternative_plan_general_url}: {alternative_plan}')

    # Keeping the same addons. We might need to change this.

    selected_addon_plans = addon_plans_from_dict(
        request.session.get(
            '{0}-{1}-{2}'.format(quote_request_form_data['quote_store_key'], plan['unique_url'], "addon-plans"), [])
    )

    # Saving the currently selected addons in the session for alternative plan dictionary to avoid addon mismatch.
    request.session['{0}-{1}-{2}'.format(quote_request_form_data['quote_store_key'],
                                         alternative_plan['unique_url'], "addon-plans")] = [
        addon_plan.data_as_dict() for addon_plan in selected_addon_plans
    ]

    # Also saving the currently used addons into general url dictionary as the next stm plan function call only has
    # general url

    request.session['{0}-{1}-{2}'.format(quote_request_form_data['quote_store_key'],
                                         alternative_plan['general_url'], "addon-plans")] = [
        addon_plan.data_as_dict() for addon_plan in selected_addon_plans
    ]

    # Changing the preference of the user.
    # We need to change the preference data in this function. # TODO

    # The following three lines should be changed into a function.
    quote_request_preference_data = request.session.get('quote_request_preference_data', {})
    quote_request_preference_data[stm_name]['Duration_Coverage'] = [coverage_duration]  # why not a dict of str Need to refractor.

    try:
        if not changed_coinsurance_percentage:
            quote_request_preference_data[stm_name]['Coinsurance_Percentage'] = [plan['Coinsurance_Percentage']]
        else:
            quote_request_preference_data[stm_name]['Coinsurance_Percentage'] = [changed_coinsurance_percentage]

        if not changed_benefit_amount:
            quote_request_preference_data[stm_name]['Benefit_Amount'] = [plan['Benefit_Amount']]
        else:
            quote_request_preference_data[stm_name]['Benefit_Amount'] = [changed_benefit_amount]

        if not changed_coverage_maximum:
            quote_request_preference_data[stm_name]['Coverage_Max'] = [plan['Coverage_Max']]
        else:
            quote_request_preference_data[stm_name]['Coverage_Max'] = [changed_coverage_maximum]


    except KeyError as k:
        logger.warning(f'======>{k}')

    request.session['quote_request_preference_data'] = quote_request_preference_data

    logger.info(f'PLAN: {alternative_plan}')
    logger.info("ADD-ON: {0}".format([s_add_on_plan.data_as_dict() for s_add_on_plan in selected_addon_plans]))
    # return render(request, 'quotes/stm_plan_apply.html',
    #               {'plan': alternative_plan, 'quote_request_form_data': quote_request_form_data,
    #                'selected_addon_plans': selected_addon_plans})
    return JsonResponse(
        {
            'status': 'success',
            'url': reverse('quotes:stm_plan', kwargs={'plan_url': alternative_plan_general_url})
        }
    )


def legal(request, slug):
    try:
        template_response = render(request, 'quotes/pages/legal/{0}.html'.format(slug),
                                   {'slug': slug, "metaDesc": None, })
    except TemplateDoesNotExist:
        raise Http404()

    meta = ""
    metablog = [d for d in legal_page_info if d['slug'] == slug]
    if (len(metablog) > 0):
        meta = metablog[0]['meta']
        template_response = render(request, "quotes/pages/legal/{0}.html".format(slug),
                                   {"slug": slug, "metaDesc": meta, })
        print(template_response)

    else:

        return template_response

    return template_response


def life_insurance(request):
    return render(request, 'quotes/lifeinsurance.html')


def check_stm_available_in_state(request: WSGIRequest) -> JsonResponse:
    stm_dictionary = settings.STATE_SPECIFIC_PLAN_DURATION
    stm_dict_values = stm_dictionary.values()
    stm_available_states = set().union(*[*stm_dict_values])

    form_data = request.session.get('quote_request_form_data', None)
    if form_data is not None:
        user_state = form_data['State']
        if user_state in stm_available_states:
            return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'fail'})


