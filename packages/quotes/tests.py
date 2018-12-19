from django.test import TestCase, Client

from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware


import random
import datetime

# from .models import
from django.urls import reverse

from quotes.views import stm_plan, stm_apply


class STMPlanTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test(self):

        random_year = random.choice(range(1956, 1996))
        random_gender = random.choice(['Male', 'Female'])
        random_tobacco = random.choice(['Y', 'N'])
        tomorrow_date = datetime.date.today() + datetime.timedelta(days=1)
        random_state_zip_combo = random.choice([
            ('OH', '44102'),
            ('WV', '24867'),
            ('FL', '33129')
        ])
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


        request = self.factory.post('/health-insurance-quotes/', post_data)

        plan_url = 'LifeShield_STM-wv-1000-4000-250000-50-3*1p2'

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

                                   'Zip_Code': '24867',
                                   'Spouse_DOB': None,
                                   'State': 'WV',
                                   'Spouse_Gender': '',

                                   'Applicant_Gender': 'Male',
                                   'Last_Name': ''}

        request = self.factory.post(reverse('quotes:plan_quote', args=['stm']))

        setattr(request,
                'session' ,
                {'quote_request_response_data': {},
                 'quote_request_formset_data': [],

                 'active_featured_stm_plan_quote_nha': False,
                 'applicant_enrolled': False,

                 'quote_request_form_data': quote_request_form_data,

                 'featured_stm_plan_quote_nha_try_count': 0})



        middleware = SessionMiddleware()
        middleware.process_request(request)

        response = stm_plan(request, plan_url)

        self.assertEqual(response.status_code, 302)
        print(f'{response.content}')





