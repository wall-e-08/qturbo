import json

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .redisqueue import redis_connect
from .utils import (form_data_is_valid)
from .logger import VimmLogger
from .tasks import StmPlanTask

logger = VimmLogger('quote_turbo')

json_decoder = json.JSONDecoder()
json_encoder = json.JSONEncoder()
redis_conn = redis_connect()


def home(request):
    return render(request, 'quotes/landing_page.html', {})

def plans(request, zip_code=None):
    pass
    # """
    # This is the view that shows up to gather users information
    # and then we click Compare Health Insurance button to start asking
    # for quotes.
    # :param request: Django request object
    # :param zip_code: zip code for area for which quote is given
    # :type zip_code: str
    # :return: Django HttpResponse Object
    # """
    # # session bug fixed
    # # anonymous session is created if there is a true need
    # quote_request_form_data = {}
    # if request.session._get_session_key() is not None:
    #     quote_request_form_data = request.session.get('quote_request_form_data', {})
    #     # Amir Bhai's change for checking Ins type
    #     # quote_request_form_data['Ins_Type'] = 'lim'
    # else:
    #     request.session['quote_request_formset_data'] = quote_request_form_data
    #     request.session.modified = True
    # print('\n90 quote_request_form_data: ', quote_request_form_data)
    # if quote_request_form_data:
    #     quote_request_formset_data = request.session.get('quote_request_formset_data', [])
    # else:
    #     quote_request_formset_data = []
    #
    # if quote_request_form_data and form_data_is_valid(quote_request_form_data) == False:
    #     quote_request_form_data = {}
    #     quote_request_formset_data = []
    #     request.session['quote_request_form_data'] = {}
    #     request.session['quote_request_formset_data'] = []
    #
    # if quote_request_form_data and quote_request_formset_data:
    #     if quote_request_form_data['Children_Count'] != len(quote_request_formset_data):
    #         quote_request_formset_data = []
    #         quote_request_form_data['Children_Count'] = 0
    #
    # form = None
    # formset = None
    # if quote_request_form_data and (zip_code is None or quote_request_form_data.get('Zip_Code') == zip_code):
    #     form = ApplicantInfoForm(initial=quote_request_form_data)
    #     logger.info("{0}".format(quote_request_form_data))
    #
    # if zip_code:
    #     zip_form = ZipCodeForm({'zip_code': zip_code})
    #     if zip_form.is_valid():
    #         zip_code = zip_form.cleaned_data['zip_code']
    #     else:
    #         return HttpResponseRedirect(reverse('healthplans:plans'))
    #
    # if form is None:
    #     quote_request_formset_data = []
    #     effective_date = (timezone.now() + datetime.timedelta(
    #         days=1, minutes=settings.EFFECTIVE_DATE_OFFSET_BY_MINUTES)).date()
    #     if effective_date.day > 28:
    #         effective_date = datetime.date(
    #             year=(effective_date.year if effective_date.month < 12 else effective_date.year + 1),
    #             month=((effective_date.month + 1) if effective_date.month < 12 else 1),
    #             day=1
    #         )
    #     form = ApplicantInfoForm(
    #         initial={
    #             'Ins_Type': 'lim',
    #             'Payment_Option': '1',
    #             'Effective_Date': effective_date,
    #             'Tobacco': 'N'
    #         }
    #     )
    # if quote_request_formset_data:
    #     formset = ChildInfoFormSet(initial=quote_request_formset_data)
    # if formset is None:
    #     formset = ChildInfoFormSet()
    #
    # print('\n\nplans: quote_request_form_data:', quote_request_form_data)
    # return render(request, 'healthplans/plans.html',
    #               {"zip_code": zip_code, "form": form, 'formset': formset})
    return render(request, 'quotes/landing_page.html')  # TODO



def survey_members(request):
    return render(request, 'quotes/survey/members.html', {})


def plan_quote(request, ins_type):
    """

    :param request: Django request object
    :param ins_type: stm/lim/anc
    :return: Django HttpResponse Object
    """
    '''Testing'''
    post_data_zip_code = request.POST.get("zip_code", "")
    print("post_data_zip_code: ", post_data_zip_code)

    """
    We see that post data is not working. We are writing some 
    dummy variables to test the view functions. Then we shall
    write vue getter methods to pass data.
    """
    # 'quote_request_form_data': {'Payment_Option': '1', 'applicant_is_child': False, 'Tobacco': 'N',
    #                             'Dependents': [], 'Ins_Type': 'stm', 'Coverage_Days': None, 'First_Name': '',
    #                             'Children_Count': 0, 'Applicant_Age': 40, 'Address1': '',
    #                             'Applicant_DOB': '10-18-1978', 'Spouse_Age': None, 'Include_Spouse': 'No',
    #                             'quote_request_timestamp': 1541930336, 'Email': '', 'Effective_Date': '11-12-2018',
    #                             'Phone': '', 'quote_store_key': '24867-10-18-1978-Male-1-11-12-2018-N-stm',
    #                             'Zip_Code': '24867', 'Spouse_DOB': None, 'State': 'WV', 'Spouse_Gender': '',
    #                             'Applicant_Gender': 'Male', 'Last_Name': ''}
    #

    quote_request_form_data = {
        'Zip_Code' : '44102',
        'Applicant_DOB' : '10-18-1992',
        'Applicant_Gender' : 'Male',
        'Tobacco' : 'N'
    }




    # quote_request_form_data = {} # TODO
    print("Insurance type is {0}".format(ins_type))
    # quote_request_form_data = request.session.get('quote_request_form_data', {})
    request.session['applicant_enrolled'] = False
    request.session.modified = True
    # if quote_request_form_data.get('applicant_is_child', True): # TODO
    #     request.session['quote_request_formset_data'] = []

    # TODO
    # if quote_request_form_data and form_data_is_valid(quote_request_form_data) == False:
    #     quote_request_form_data = {}
    #     request.session['quote_request_form_data'] = {}
    #     request.session['quote_request_formset_data'] = []
    #     request.session['quote_request_response_data'] = {}

    # if not quote_request_form_data:
    # WE HAVE TO DO SOMETHING
    #     return HttpResponseRedirect(reverse('quotes:plans', args=[]))

    # TODO
    # quote_request_form_data['Ins_Type'] = ins_type
    # logger.info("Plan Quote For Data: {0}".format(quote_request_form_data))

    d = {'monthly_plans': [], 'addon_plans': []}
    request.session['quote_request_response_data'] = d
    request.session.modified = True
    # logger.info("PLAN QUOTE LIST - form data: {0}".format(quote_request_form_data))

    """ Changing quote store key regarding insurance type  """
    # if ins_type == "stm":
    #     quote_request_form_data['quote_store_key'] = quote_request_form_data['quote_store_key'][:-3] + 'stm'
    # elif ins_type == "lim":
    #     quote_request_form_data['quote_store_key'] = quote_request_form_data['quote_store_key'][:-3] + 'lim'
    # elif ins_type == "anc":
    #     quote_request_form_data['quote_store_key'] = quote_request_form_data['quote_store_key'][:-3] + 'anc'

    """ Calling celery for populating quote list """
    # redis_key = "{0}:{1}".format(request.session._get_session_key(),
    #                              quote_request_form_data['quote_store_key'])
    logger.info("465: Calling celery task for ins_type: {0}".format(ins_type))
    # logger.info("redis_key: {0}".format(redis_key))
    #
    # logger.info('\n\nquote_request_form_data: {0}'.format(quote_request_form_data))
    # if not redis_conn.exists(redis_key):
    #     redis_conn.rpush(redis_key, *[json_encoder.encode('START')])
    #
    #     if ins_type == 'stm':
    #         StmPlanTask.delay(request.session.session_key, quote_request_form_data)
        # elif ins_type == 'lim':
        #     LimPlanTask.delay(request.session.session_key, quote_request_form_data)
        # elif ins_type == 'anc':
        #     AncPlanTask.delay(request.session.session_key, quote_request_form_data)


    return render(request, 'quotes/quote_list.html', {
        'form_data': quote_request_form_data, 'xml_res': d
    })
