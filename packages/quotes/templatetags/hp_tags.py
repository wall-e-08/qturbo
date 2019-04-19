# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import re
import json
import decimal
import logging
import datetime
from django import template
from collections import deque
from django.template import Context

from dateutil.relativedelta import relativedelta

from quotes.utils import parse_stm_duration
from quotes.addon_properties import properties as addon_props


logger = logging.getLogger('main.quotes.templatetags.hp_tags')


json_encoder = json.JSONEncoder()


register = template.Library()


QR_DATE_PATTERN = re.compile(r'^(\d{2})-(\d{2})-(\d{4})$')

ER_DATE_PATTERN = re.compile(r'^(\d{4})-(\d{2})-(\d{2})$')

PREFIX = {1: 'st', 2: 'nd', 3: 'rd', 21: 'st', 22: 'nd', 23: 'rd', 31: 'st'}


@register.simple_tag
def form_date_field_value(value):
    logger.debug("type of value \"{0}\"; value: {1}".format(type(value), value))
    if value is None:
        return ""
    if isinstance(value, datetime.date):
        return value.strftime("%m/%d/%Y")
    if not isinstance(value, str):
        return value
    return QR_DATE_PATTERN.sub(r'\1/\2/\3', value)


@register.simple_tag
def form_date_field_value_e(value):
    logger.debug("type of value \"{0}\"; value: {1}".format(type(value), value))
    if value is None:
        return ""
    if isinstance(value, datetime.date):
        return value.strftime("%m/%d/%Y")
    if not isinstance(value, str):
        return value
    print(value)
    return ER_DATE_PATTERN.sub(r'\2/\3/\1', value)


@register.filter
def plan_name_for_img(value):
    return value.lower().replace(' ', '-')


@register.simple_tag
def int_to_time(value):
    logger.debug("type of value \"{0}\"; value: {1}".format(type(value), value))
    if value is None: return "00:00"
    parts = deque()
    while value >= 60:
        value, part = divmod(value, 60)
        parts.appendleft('{0:0>2}'.format(part))
    parts.appendleft('{0:0>2}'.format(value))
    if len(parts) == 1:
        parts.appendleft('00')
    return ':'.join(parts)


@register.filter
def qeadcs(value):
    return round(12/int(value))


@register.simple_tag(takes_context=True)
def wrong_answer_none(context, question):
    try:
        wrong_ans_question = next(filter(lambda q: q['user_answer'] == q['CorrectAnswer'], context['stm_questions']))
    except StopIteration:
        return ''
    if wrong_ans_question['order'] < question['order']:
        return 'wrong_ans_none'
    return ''


@register.simple_tag(takes_context=True)
def pre_qus_ans_is_correct(context, order):
    try:
        pre_question = next(filter(lambda q: q['g_order'] == (order - 1), context['stm_questions']))
    except StopIteration:
        return False

    if pre_question['user_answer'] and pre_question['user_answer'] == pre_question['CorrectAnswer']:
        return False

    return pre_question['user_answer'] in pre_question['ExpectedAnswers']


@register.simple_tag(takes_context=True)
def any_wrong_answer(context):
    try:
        next(filter(
            lambda q: (q['user_answer'] is not None and q['user_answer'] == q['CorrectAnswer']),
            context['stm_questions']
        ))
    except StopIteration:
        return False
    return True


@register.simple_tag(takes_context=True)
def all_questions_answered(context):
    try:
        next(filter(lambda q: q['user_answer'] is None, context['stm_questions']))
    except StopIteration:
        return True
    return False


@register.tag
def stm_plan_feature(parser, token):
    try:
        tag_name, stm_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0]
        )
    return StmPlanFeatureNode(stm_name)


class StmPlanFeatureNode(template.Node):

    def __init__(self, stm_name):
        self.stm_name = template.Variable(stm_name)

    def render(self, context):
        try:
            actual_stm_name = self.stm_name.resolve(context)
        except template.VariableDoesNotExist:
            if context.template.engine.debug:
                raise
            return ''
        t = context.template.engine.get_template(
            'quotes/tags/{0}.html'.format(actual_stm_name.lower().replace(' ', '_'))
        )
        return t.render(Context({'var': context.get('plan')}, autoescape=context.autoescape))


@register.tag
def stm_plan_info(parser, token):
    print('stm_plan_info', token)
    try:
        tag_name, stm_plan = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0]
        )
    return StmPlanInfoNode(stm_plan)


class StmPlanInfoNode(template.Node):

    def __init__(self, stm_plan):
        print('StmPlanInfoNode', stm_plan)
        self.stm_plan = template.Variable(stm_plan)

    def render(self, context):
        try:
            actual_stm_plan = self.stm_plan.resolve(context)
        except template.VariableDoesNotExist:
            if context.template.engine.debug:
                raise
            return ''
        t = context.template.engine.get_template(
            'quotes/tags/{0}_info.html'.format(actual_stm_plan['Name'].lower().replace(' ', '_'))
        )
        print('related_plans: ',  context.get('related_plans'))
        return t.render(Context({'plan': actual_stm_plan, 'form_data': context.get('form_data'),
                                 'related_plans': context.get('related_plans')},
                                autoescape=context.autoescape))


@register.simple_tag(takes_context=True)
def plan_coverage_end_date(context):
    try:
        quote_request_form_data = context['quote_request_form_data']
    except KeyError:
        quote_request_form_data = context['form_data']
    if quote_request_form_data['Payment_Option'] == '1':
        effective_date = datetime.datetime.strptime(quote_request_form_data['Effective_Date'], '%m-%d-%Y')
        plan = context['plan']
        duration = parse_stm_duration(plan['Duration_Coverage'])
        return (effective_date + relativedelta(months=int(duration))).strftime('%m/%d/%Y')      # Is casting duration necessary? -ds87
        # datetime.timedelta(days=(int(plan['Duration_Coverage']) * 30 - 1))).strftime('%m/%d/%Y')
    return quote_request_form_data['Coverage_Days'].replace('-', '/')


@register.simple_tag(takes_context=True)
def plan_single_premium(context):
    plan = context['plan']
    premium = decimal.Decimal(plan['Premium']) + decimal.Decimal(plan['Enrollment_Fee'])

    if plan['Name'] in ['HealtheMed STM', 'HealtheFlex STM', 'Sage STM']:
        premium += decimal.Decimal(plan['Administrative_Fee'])

    if plan['Name'] in ['Principle Advantage']:
        premium += decimal.Decimal(plan['TelaDocFee'])

    if plan['Name'] == 'Premier STM':
        premium += (decimal.Decimal(plan['Administrative_Fee']) +
                    decimal.Decimal(plan['GapAffordPlus_Fee']) +
                    decimal.Decimal(plan['GapAffordPlus_AdminFee']))

    if plan['Name'] == 'Everest STM':
        premium += (decimal.Decimal(plan['RxAdvocacy_Fee']) +
                    decimal.Decimal(plan['Medsense_Fee']) +
                    decimal.Decimal(plan['TelaDoc_Fee']) +
                    decimal.Decimal(plan.get('ChoiceValueSavings_Fee', '0.0')))

    return premium


@register.simple_tag(takes_context=True)
def plan_total_payment(context):
    plan = context['plan']
    selected_addon_plans = context['selected_addon_plans']
    total_payment = decimal.Decimal(plan['actual_premium']) + decimal.Decimal(plan['Enrollment_Fee'])
    for add_on_plan in selected_addon_plans:
        total_payment += decimal.Decimal(add_on_plan['actual_premium'])
    return total_payment


@register.simple_tag(takes_context=True)
def plan_actual_premium(context, stm_plan=None):
    plan = stm_plan or context['plan']
    premium = decimal.Decimal(plan['Premium'])

    if plan['Name'] in ['HealtheMed STM', 'HealtheFlex STM', 'Sage STM']:
        premium += decimal.Decimal(plan['Administrative_Fee'])

    if plan['Name'] in ['Principle Advantage']:
        premium += decimal.Decimal(plan['TelaDocFee'])

    if plan['Name'] == 'Premier STM':
        premium += (decimal.Decimal(plan['Administrative_Fee']) +
                    decimal.Decimal(plan['GapAffordPlus_Fee']) +
                    decimal.Decimal(plan['GapAffordPlus_AdminFee']))

    if plan['Name'] in ['Everest STM', 'LifeShield STM', 'AdvantHealth STM']:
        premium += (decimal.Decimal(plan['RxAdvocacy_Fee']) +
                    decimal.Decimal(plan['Medsense_Fee']) +
                    decimal.Decimal(plan['TelaDoc_Fee']) +
                    decimal.Decimal(plan.get('RealValueSavings_Fee', '0.0')) +
                    decimal.Decimal(plan.get('RealValueSavings_AdminFee', '0.00')) +
                    decimal.Decimal(plan.get('ChoiceValueSavings_Fee', '0.0')) +
                    decimal.Decimal(plan.get('ChoiceValue_AdminFee', '0.00')) +
                    decimal.Decimal(plan.get('VBP_Fee', '0.00')))

        return premium


@register.simple_tag(takes_context=True)
def premier_admin_fee(context):
    plan = context['plan']

    if plan['Name'] == 'Premier STM':
        return (decimal.Decimal(plan['Administrative_Fee']) +
                decimal.Decimal(plan['GapAffordPlus_Fee']) +
                decimal.Decimal(plan['GapAffordPlus_AdminFee']))

    return decimal.Decimal('0.00')


@register.simple_tag(takes_context=True)
def everest_admin_fee(context):
    plan = context['plan']
    if plan['Name'] == 'Everest STM':
        return (decimal.Decimal(plan['RxAdvocacy_Fee']) +
                decimal.Decimal(plan['Medsense_Fee']) +
                decimal.Decimal(plan['TelaDoc_Fee']) +
                decimal.Decimal(plan.get('ChoiceValueSavings_Fee', '0.0')))
    return decimal.Decimal('0.00')


@register.simple_tag
def plan_start_day(value):
    effective_date = datetime.datetime.strptime(value, '%m-%d-%Y')
    return "{0}{1}".format(effective_date.day, PREFIX.get(effective_date.day, 'th'))


@register.filter
def jsonify(value):
    if isinstance(value, (dict, list, tuple)):
        return json_encoder.encode(value)
    return value


@register.filter
def add_on_name_for_brochure(value):
    return value.replace(' ', '-')


@register.filter
def slug_pdfied(value):
    addon_dict = {
        # Todo: Ally rx/ Freedom platinum

        "dental-savings": "Dental-Savings",
        "foundation-dental": "Foundation-Dental",
        "foundation-vision": "Foundation-Vision",
        "freedom-spirit": "Freedom-Spirit",
        "freedom-spirit-plus": "Freedom-Spirit-Plus",
        "safeguard-critical-illness": "Safeguard-Critical-Illness",
        "sentry-accident-plan": "Sentry-Accident-Plan",
        "usa+-dental": "USA+-Dental",

    }

    return addon_dict[value]


@register.filter
def plan_duration_month(value):
    # TODO: Handle exceptions
    month_times = value.split("*")
    return month_times[0]


@register.filter
def plan_duration_total_month(value):
    # TODO: Handle exceptions
    month_times = value.split("*")
    return int(month_times[0]) * int(month_times[1])


@register.simple_tag
def addon_disclaimers(addons):
    if not (isinstance(addons, set) or isinstance(addons, list)):
        return None
    data = {}
    for add_on in addons:
        addon_id = str(add_on.get('addon_id')) if isinstance(addons, list) else add_on.addon_id
        aop = addon_props.get(addon_id)
        if aop:
            try:
                discl = aop['disclaimer']
                if bool(discl and discl.strip()):
                    data[aop['name']] = discl
            except KeyError as er:
                print("err in addon_disclaimer: {}".format(er))
    print(data)
    return data



@register.simple_tag(takes_context=True)
def get_underwritten_info(context):
    try:
        plan = context['plan']['Name']
    except (AttributeError, TypeError, KeyError) as err:
        print("hp_tags error: {}".format(err))
        return None
    data = {
        "AdvantHealth_STM": "AdvantHealth STM is underwritten by American Financial Security Life Insurance Company",
        "Legion_Limited_Medical": "Legion Limited Medical is underwritten by AXIS Insurance Company",
        "VitalaCare": "VitalaCare is underwritten by LifeShield National Insurance Co",
        "LifeShield_STM": "LifeShield STM is underwritten by LifeShield National Insurance Co."
    }
    print(data.get(plan.replace(' ', '_')))
    return data.get(plan.replace(' ', '_'))




