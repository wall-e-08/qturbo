import json

import random
import datetime

from django.test import RequestFactory

from quotes.views import check_stm_available_in_state

# Set up pytest using pytest.ini first

def get_request(
        state='OH',
        zip='44102'
):
    random_year = random.choice(range(1956, 1996))
    random_gender = random.choice(['Male', 'Female'])
    random_tobacco = random.choice(['Y', 'N'])
    tomorrow_date = datetime.date.today() + datetime.timedelta(days=1)
    random_state_zip_combo = random.choice([
        ('OH', '44102'),
        ('WV', '24867'),
        ('FL', '33129')
    ])

    factory = RequestFactory()
    random_ins_type = random.choice([
        'stm',
        'lim',
        'anc'
    ])

    post_data = {'Children_Count': ['0'],
                 'Include_Spouse': ['No'],
                 'Ins_Type': ['stm'],

                 'child-TOTAL_FORMS': ['0'],
                 'Applicant_Gender': ['Female'],
                 'child-INITIAL_FORMS': ['0'],

                 'Tobacco': ['N'],
                 'csrfmiddlewaretoken': ['AKcf7PmvM5hRAA97dyo5TR18J5Q1qY0b'],
                 'Payment_Option': ['1'],

                 'child-MIN_NUM_FORMS': ['0'],
                 'Applicant_DOB': ['10/18/1978'],
                 'Zip_Code': ['24867'],
                 'child-MAX_NUM_FORMS': ['9'],

                 'Effective_Date': [tomorrow_date.strftime("%m/%d/%Y")]
                 }


    request = factory.post('/health-insurance-quotes/', post_data)

    quote_request_form_data = {'Payment_Option': '1',
                               'applicant_is_child': False,
                               'Tobacco': 'N',

                               'Dependents': [],
                               'Ins_Type': 'stm',
                               'Coverage_Days': None,
                               'First_Name': '',

                               'Children_Count': 0,
                               'Applicant_Age': 40,
                               'Address1': '',

                               'Applicant_DOB': '10-18-1978',
                               'Spouse_Age': None,
                               'Include_Spouse': 'No',

                               'quote_request_timestamp': 1541930336,
                               'Email': '',
                               'Effective_Date': tomorrow_date.strftime("%m/%d/%Y"),

                               'Phone': '',
                               'quote_store_key': '24867-10-18-1978-Male-1-11-12-2018-N-stm',

                               'Zip_Code': zip,
                               'Spouse_DOB': None,
                               'State': state,
                               'Spouse_Gender': '',

                               'Applicant_Gender': 'Male',
                               'Last_Name': ''}
    setattr(request,
            'session',
            {'quote_request_response_data': {},
             'quote_request_formset_data': [],
             'active_featured_stm_plan_quote_nha': False,
             'applicant_enrolled': False,
             'quote_request_form_data': quote_request_form_data,
             'featured_stm_plan_quote_nha_try_count': 0})

    return request

def test_check_stm_available_in_texas():

    request = get_request(state='TX', zip='79499')

    response = check_stm_available_in_state(request)
    assert response.status_code == 200
    assert response.content.decode() == '{"status": "success"}'

def test_check_stm_available_in_ohio():

    request = get_request()

    response = check_stm_available_in_state(request)
    assert response.status_code == 200
    assert response.content.decode() == '{"status": "fail"}'

def test_check_stm_available_in_florida():

    request = get_request(state='FL', zip='33129')

    response = check_stm_available_in_state(request)
    assert response.status_code == 200
    assert response.content.decode() == '{"status": "success"}'









