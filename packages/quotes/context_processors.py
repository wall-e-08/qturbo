from __future__ import unicode_literals, print_function

from .utils import form_data_is_valid
import quotes.models as qm
from django.core.exceptions import ObjectDoesNotExist

# For static type checking.
from django.http.request import HttpRequest
from dashboard.models import Menu


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


def menu_context(request):
    header_main_menu = Menu.objects.filter(parent_menu=None, position='top').order_by('id')
    footer_main_menu = Menu.objects.filter(parent_menu=None, position='btm').order_by('id')
    header_menu = []
    footer_menu = []
    for hm in header_main_menu:
        child_menu = Menu.objects.filter(parent_menu=hm)
        header_menu.append({
            "parent": hm,
            "child": child_menu
        })
    for fm in footer_main_menu:
        child_menu = Menu.objects.filter(parent_menu=fm)
        footer_menu.append({
            "parent": fm,
            "child": child_menu
        })
    return {
        "header_menu": header_menu,
        "footer_menu": footer_menu,
    }
