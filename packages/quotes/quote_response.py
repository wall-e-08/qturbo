from __future__ import unicode_literals, print_function

import re
import html
import copy
import decimal
import xml.etree.ElementTree as ET

from core import settings
from quotes.addon_properties import properties as add_on_properties, carrier_id as add_on_carrier_id


ADDON_ID_PATTERN = re.compile(r'^ID(?P<addon_id>\d+)$')
MONTH_OPTION_PATTERN = re.compile(r'^Option(?P<option>\d+)$')


class LimQuoteResponse(object):

    special_tags = ['Quote_ID', 'Quote', 'Access_Token']

    def __init__(self, stm_name, xml_text, state, plan_id, quote_request_timestamp, request_data_combination):
        self.stm_name = stm_name
        self.State = state
        self.xml_text = xml_text
        self.Plan_ID = plan_id
        self.quote_request_timestamp = quote_request_timestamp
        self.request_data_combination = request_data_combination

        self.escaped_xml_text = xml_text.replace('&', '&amp;').replace('"', '&quot;').replace("'", '&#39;')
        # MEMORY_EXHAUSTIVE print("LIM QUOTE RESPONSE - {2} - {0} : {1}".format(self.request_data_combination, self.escaped_xml_text, self.stm_name))
        self.root = ET.fromstring(self.escaped_xml_text)

        self.Quote_ID = None
        self.Quote_ID = (self.root.find('Quote_ID').text
                         if isinstance(self.root.find('Quote_ID'), ET.Element) else None)
        if self.Quote_ID is None:
            self.Quote_ID = (self.root.find('Quote').text
                             if isinstance(self.root.find('Quote'), ET.Element) else None)

        self.Access_Token = (self.root.find('Access_Token').text
                             if isinstance(self.root.find('Access_Token'), ET.Element) else None)

        self.monthly = []
        self.addon_plans = []
        self.errors = []
        self.process()

    def process(self):
        processors = {
            'PlanCost': self.process_plan_cost,
            'Add-ons': self.process_addon,
            'Error': self.process_error
        }
        for child in self.root:
            try:
                processors[child.tag.replace("_", '')](child)
            except KeyError:
                if child.tag not in self.special_tags:
                    raise

    def process_plan_cost(self, plan_cost_tree):
        attrs = {'Quote_ID': self.Quote_ID,
                 'Plan_ID': self.Plan_ID,
                 'Access_Token': self.Access_Token,
                 'stm_name': self.stm_name,
                 'state': self.State,
                 'quote_request_timestamp': self.quote_request_timestamp}
        plans = []
        for child in plan_cost_tree:
            if not child.tag.startswith('Plan'):
                continue
            plan = {"Plan_Name": child.tag}
            for quote in child:
                plan[quote.tag] = str(quote.text)
            plans.append(plan)
        for p in plans:
            p.update(copy.deepcopy(attrs))
            if p.get('Plan_Name', '') == 'Plan_9':
                continue
            self.monthly.append(LimitedPlan(**p))

    def process_addon(self, addons_tree):
        for child in addons_tree:
            match = ADDON_ID_PATTERN.match(child.tag)
            if match:
                self.process_addon_id(match.groupdict()['addon_id'], child)

    def process_addon_id(self, addon_id, addon_id_tree):
        for child in addon_id_tree:
            self.process_addon_plan(addon_id, child)

    def process_addon_plan(self, addon_id, plan_tree):
        plan = AddonPlan(self.stm_name, addon_id, plan_tree=plan_tree)
        plan.quote_response = self
        self.addon_plans.append(plan)

    def process_error(self, error_tree):
        error_message = error_tree.find('Message').text if isinstance(error_tree.find('Message'), ET.Element) else ''
        self.errors = error_message.strip().split('#')


# ancillaries
class AncillariesQuoteResponse(object):

    special_tags = ['Quote_ID', 'Quote', 'Access_Token', 'Note']

    is_standalone = True

    def __init__(self, stm_name, xml_text, state, plan_id, quote_request_timestamp,
                                  quote_store_key):
        self.stm_name = stm_name
        self.State = state
        self.xml_text = xml_text
        self.Plan_ID = plan_id
        self.quote_request_timestamp = quote_request_timestamp
        self.quote_store_key = quote_store_key # Is this needed

        self.Ins_Type = 'anc'

        self.escaped_xml_text = xml_text.replace('&', '&amp;').replace('"', '&quot;').replace("'", '&#39;')
        print("Parsed and Formatted Quote Plan XML response for {1}:\n AncillariesQuoteResponse_XML:{0}".format(self.escaped_xml_text, self.stm_name))
        self.root = ET.fromstring(self.escaped_xml_text)

        self.Quote_ID = None
        self.Quote_ID = (self.root.find('Quote_ID').text
                         if isinstance(self.root.find('Quote_ID'), ET.Element) else None)
        if self.Quote_ID is None:
            self.Quote_ID = (self.root.find('Quote').text
                             if isinstance(self.root.find('Quote'), ET.Element) else None)

        self.Access_Token = (self.root.find('Access_Token').text
                             if isinstance(self.root.find('Access_Token'), ET.Element) else None)

        self.note = (self.root.find('Note').text
                             if isinstance(self.root.find('Note'), ET.Element) else None)

        self.monthly = []
        self.addon_plans = []
        self.errors = []
        self.process()

    def process(self):
        processors = {
            'PlanCost': self.process_plan_cost,
            'Add-ons': self.process_addon,
            'Error': self.process_error
        }
        for child in self.root:
            try:
                processors[child.tag.replace("_", '')](child)
            except KeyError:
                if child.tag not in self.special_tags:
                    pass

    def process_plan_cost(self, plan_cost_tree):
        attrs = {'Quote_ID': self.Quote_ID,
                 'Plan_ID': self.Plan_ID,
                 'Access_Token': self.Access_Token,
                 'stm_name': self.stm_name,
                 'note': self.note,
                 'state': self.State,
                 'quote_request_timestamp': self.quote_request_timestamp,
                 }
        plans = []
        for child in plan_cost_tree:
            plan = {"Plan_Name": child.tag}
            for quote in child:
                plan[quote.tag] = str(quote.text)

            plans.append(plan)
        for p in plans:
            p.update(copy.deepcopy(attrs))
            print('AncillariesQuoteResponse for {1}. individual_plans: {0}'.format(p, self.stm_name))
            if p.get('Plan_Name', '') == 'Plan_9':
                continue

            self.monthly.append(LimitedPlan(**p))

    def process_addon(self, addons_tree):
        for child in addons_tree:
            match = ADDON_ID_PATTERN.match(child.tag)
            if match:
                self.process_addon_id(match.groupdict()['addon_id'], child)

    def process_addon_id(self, addon_id, addon_id_tree):
        for child in addon_id_tree:
            self.process_addon_plan(addon_id, child)

    def process_addon_plan(self, addon_id, plan_tree):
        plan = AddonPlan(self.stm_name, addon_id, plan_tree=plan_tree)
        plan.quote_response = self
        self.addon_plans.append(plan)

    def process_error(self, error_tree):
        error_message = error_tree.find('Message').text if isinstance(error_tree.find('Message'), ET.Element) else ''
        self.errors = error_message.strip().split('#')



class PrincipleResponse(LimQuoteResponse):
    pass


class CardinalResponse(LimQuoteResponse):
    pass


class VitalaCareResponse(LimQuoteResponse):
    pass


class HealthChoiceResponse(LimQuoteResponse):
    pass


class LegionLimitedMedicalResponse(LimQuoteResponse):
    pass


class USADentalResponse(AncillariesQuoteResponse):
    pass


class FoundationDentalResponse(object):

    special_tags = ['Quote_ID', 'Quote', 'Access_Token', 'EnrollmentFee', 'AdministrativeFee']

    is_standalone = True

    def __init__(self, stm_name, xml_text, state, plan_id, quote_request_timestamp,
                 request, product_type='main'):
        self.stm_name = stm_name
        self.State = state
        self.xml_text = xml_text
        self.Plan_ID = plan_id
        self.quote_request_timestamp = quote_request_timestamp
        self.request = request
        self.product_type = product_type

        note = 1
        while note < 3:
            NoteStartIndex = xml_text.find('<Note>')
            if not NoteStartIndex:
                break
            NoteEndIndex = xml_text.find('</Note>')
            substring = xml_text[NoteStartIndex:NoteEndIndex + 7]
            xml_text = xml_text.replace(substring, '')
            note += 1

        self.escaped_xml_text = xml_text.replace('&', '&amp;').replace('"', '&quot;').replace("'", '&#39;').replace('Protector I', 'Protector_I')
        print("Parsed and Formatted Quote Plan XML response, FoundationDentalResponse_XML: {0}, user_info: {1}".format(self.escaped_xml_text, self.request))
        self.root = ET.fromstring(self.escaped_xml_text)

        self.Quote_ID = None
        self.Quote_ID = (self.root.find('Quote_ID').text
                         if isinstance(self.root.find('Quote_ID'), ET.Element) else None)
        if self.Quote_ID is None:
            self.Quote_ID = (self.root.find('Quote').text
                             if isinstance(self.root.find('Quote'), ET.Element) else None)

        self.Access_Token = (self.root.find('Access_Token').text
                             if isinstance(self.root.find('Access_Token'), ET.Element) else None)

        self.Enrollment_Fee = (self.root.find('EnrollmentFee').text
                               if isinstance(self.root.find('EnrollmentFee'), ET.Element) else None)

        self.Administrative_Fee = (self.root.find('AdministrativeFee').text
                               if isinstance(self.root.find('AdministrativeFee'), ET.Element) else None)

        self.monthly = []
        self.addon_plans = []
        self.errors = []
        self.process()

    def process(self):
        processors = {
            'PlanCost': self.process_plan_cost,
            'Add-ons': self.process_addon,
            'Error': self.process_error
        }
        for child in self.root:
            try:
                processors[child.tag.replace("_", '')](child)
            except KeyError:
                if child.tag not in self.special_tags:
                    pass

    def process_plan_cost(self, plan_cost_tree):
        if self.product_type == 'add_on':
            attrs = {'Quote_ID': self.Quote_ID,
                     'addon_id': self.Plan_ID,
                     'Access_Token': self.Access_Token,
                     'carrier_name': self.stm_name,
                     'state': self.State,
                     'quote_request_timestamp': self.quote_request_timestamp,
                     'AdministrativeFee': self.Administrative_Fee,
                     'EnrollmentFee': self.Enrollment_Fee,
                     'is_standalone': self.is_standalone,
                     }
        else:
            attrs = {'Quote_ID': self.Quote_ID,
                     'Plan_ID': self.Plan_ID,
                     'Access_Token': self.Access_Token,
                     'stm_name': self.stm_name,
                     'state': self.State,
                     'quote_request_timestamp': self.quote_request_timestamp,
                     'AdministrativeFee': self.Administrative_Fee,
                     'EnrollmentFee': self.Enrollment_Fee
                     }
        attrs.update({'carrier_plan_id': self.carrier_plan_id,
                      'carrier_id': self.carrier_plan_id,
                      })
        plans = []
        for child in plan_cost_tree:

            plan = {"Plan_Name": child.tag, 'Premium': child.text}
            if self.product_type == 'add_on':
                plan.update({'Name': '{}~~{}'.format(self.stm_name, child.tag)})
            for quote in child:
                plan[quote.tag] = str(quote.text)
            plans.append(plan)
        for p in plans:
            p.update(copy.deepcopy(attrs))
            print('LimQuoteResponse, individual_plans:{0}, user_info: {1}'.format(p, self.request))
            if p.get('Plan_Name', '') == 'Plan_9':
                continue
            print('p: {}'.format(p))
            if self.product_type == 'add_on':
                self.monthly.append(AddonPlan(**p))
            else:
                self.monthly.append(LimitedPlan(**p))

    def process_addon(self, addons_tree):
        for child in addons_tree:
            match = ADDON_ID_PATTERN.match(child.tag)
            if match:
                self.process_addon_id(match.groupdict()['addon_id'], child)

    def process_addon_id(self, addon_id, addon_id_tree):
        for child in addon_id_tree:
            self.process_addon_plan(addon_id, child)

    def process_addon_plan(self, addon_id, plan_tree):
        plan = AddonPlan(self.stm_name, addon_id, plan_tree=plan_tree)
        plan.quote_response = self
        self.addon_plans.append(plan)

    def process_error(self, error_tree):
        error_message = error_tree.find('Message').text if isinstance(error_tree.find('Message'), ET.Element) else ''
        self.errors = error_message.strip().split('#')


class FreedomSpiritPlusResponse(object):
    special_tags = ['Quote_ID', 'Quote', 'Access_Token', 'EnrollmentFee', 'AdministrativeFee']

    is_standalone = True

    def __init__(self, stm_name, xml_text, state, plan_id, quote_request_timestamp,
                 applicant_data, carrier_plan_id, product_type='main'):
        self.stm_name = stm_name
        self.State = state
        self.xml_text = xml_text
        self.Plan_ID = plan_id
        self.quote_request_timestamp = quote_request_timestamp
        self.applicant_data = applicant_data
        self.carrier_plan_id = carrier_plan_id
        self.product_type = product_type
        self.xml_tag_map = {
            '50,000': 'SPIRITPLUS_50000',
            '100,000': 'SPIRITPLUS_100000'
        }

        self.escaped_xml_text = xml_text.replace('&', '&amp;').replace('"', '&quot;').replace("'", '&#39;').replace(
            '50,000', self.xml_tag_map['50,000']).replace('100,000', self.xml_tag_map['100,000'])

        # MEMORY_EXHAUSTIVE print("Parsed and Formatted Quote Plan XML response: {0}".format(
        # MEMORY_EXHAUSTIVE            self.escaped_xml_text))
        self.root = ET.fromstring(self.escaped_xml_text)

        self.Quote_ID = None
        self.Quote_ID = (self.root.find('Quote_ID').text
                         if isinstance(self.root.find('Quote_ID'), ET.Element) else None)
        if self.Quote_ID is None:
            self.Quote_ID = (self.root.find('Quote').text
                             if isinstance(self.root.find('Quote'), ET.Element) else None)

        self.Access_Token = (self.root.find('Access_Token').text
                             if isinstance(self.root.find('Access_Token'), ET.Element) else None)

        self.Enrollment_Fee = None
        self.Enrollment_Fee = (self.root.find('EnrollmentFee').text
                               if isinstance(self.root.find('EnrollmentFee'), ET.Element) else None)

        self.Administrative_Fee = None
        self.Administrative_Fee = (self.root.find('AdministrativeFee').text
                                  if isinstance(self.root.find('AdministrativeFee'), ET.Element) else None)

        self.monthly = []
        self.addon_plans = []
        self.errors = []
        self.process()

    def process(self):
        processors = {
            'PlanCost': self.process_plan_cost,
            'Add-ons': self.process_addon,
            'Error': self.process_error
        }
        for child in self.root:
            try:
                processors[child.tag.replace("_", '')](child)
            except KeyError:
                if child.tag not in self.special_tags:
                    pass

    def process_plan_cost(self, plan_cost_tree):
        if self.product_type == 'add_on':
            attrs = {'Quote_ID': self.Quote_ID,
                     'addon_id': self.Plan_ID,
                     'Access_Token': self.Access_Token,
                     'stm_name': self.applicant_data['provider'],
                     'carrier_name': self.stm_name,
                     'state': self.State,
                     'quote_request_timestamp': self.quote_request_timestamp,
                     'AdministrativeFee': self.Administrative_Fee,
                     'Administrative_Fee': self.Administrative_Fee,
                     'EnrollmentFee': self.Enrollment_Fee,
                     'Enrollment_Fee': self.Enrollment_Fee,
                     'is_standalone': self.is_standalone,
                     }
        else:
            attrs = {'Quote_ID': self.Quote_ID,
                     'Plan_ID': self.Plan_ID,
                     'Access_Token': self.Access_Token,
                     'stm_name': self.stm_name,
                     'state': self.State,
                     'quote_request_timestamp': self.quote_request_timestamp,
                     'EnrollmentFee': self.Enrollment_Fee,
                     'Enrollment_Fee': self.Enrollment_Fee,
                     'AdministrativeFee': self.Administrative_Fee,
                     'Administrative_Fee': self.Administrative_Fee,
                     }
        attrs.update({'carrier_plan_id': self.carrier_plan_id,
                      'carrier_id': self.carrier_plan_id
                      })
        plans = []
        for child in plan_cost_tree:

            plan = {"Plan_Name": child.tag, 'Premium':  child.text}
            if self.product_type == 'add_on':
                plan.update({'Name': '{}~~{}'.format(self.stm_name, child.tag)})
            for quote in child:
                plan[quote.tag] = str(quote.text)
            plans.append(plan)

        for p in plans:

            p.update(copy.deepcopy(attrs))
            # MEMORY_EXHAUSTIVE print('AncillaryQuoteResponse for Freedom Spirit Plus:\n individual_plans: {0}'.format(p))
            if p.get('Plan_Name', '') == 'Plan_9':
                continue
            if self.product_type == 'add_on':
                self.monthly.append(AddonPlan(**p))
            else:
                self.monthly.append(LimitedPlan(**p))

    def process_addon(self, addons_tree):
        for child in addons_tree:
            match = ADDON_ID_PATTERN.match(child.tag)
            if match:
                self.process_addon_id(match.groupdict()['addon_id'], child)

    def process_addon_id(self, addon_id, addon_id_tree):
        for child in addon_id_tree:
            self.process_addon_plan(addon_id, child)

    def process_addon_plan(self, addon_id, plan_tree):
        plan = AddonPlan(self.stm_name, addon_id, plan_tree=plan_tree)
        plan.quote_response = self
        self.addon_plans.append(plan)

    def process_error(self, error_tree):
        error_message = error_tree.find('Message').text if isinstance(error_tree.find('Message'), ET.Element) else ''
        self.errors = error_message.strip().split('#')


class SafeguardCriticalIllnessResponse(AncillariesQuoteResponse):
    pass


class UnifiedResponse(LimQuoteResponse):
    pass


class LimitedPlan(object):

    def __init__(self, stm_name, state, Quote_ID, Plan_ID, Access_Token, Plan_Name, **kwargs):
        self.State = state
        self.Name = stm_name
        self.Quote_ID = Quote_ID
        self.Access_Token = Access_Token
        self.Plan_ID = Plan_ID
        self.Plan_Name = Plan_Name
        self.Ins_Type = 'lim'

        for k, v in kwargs.items():
            setattr(self, k, v)

    def __str__(self):
        return "<Limited: {0}~~{1}>".format(self.Name, self.Plan_Name)

    def __repr__(self):
        return self.__str__()

    def get_plan_name(self):
        plan_name = "{0} - {1}".format(self.Name, self.Plan_Name)
        return plan_name

    def get_unique_url(self):
        unique_url = "{0}-{1}-{2}-{3}".format(self.Name.replace(' ', '_'), self.State.lower(),
                                              self.Plan_Name, str(self.Premium).replace('.', ''))
        return unique_url

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            raise TypeError()
        return self.get_unique_url() == self.get_unique_url()

    def get_data_as_dict(self):
        data = {'Name': self.Name,
                'Plan_Name': self.Plan_Name,
                'ins_type': self.Ins_Type,
                'Premium': self.Premium,
                'unique_url': self.get_unique_url(),
                'plan_name': self.get_plan_name(),
                'Quote_ID': self.Quote_ID,
                'Access_Token': self.Access_Token,
                'Plan_ID': self.Plan_ID,
                'EnrollmentFee': getattr(self, 'EnrollmentFee', None) or getattr(self, 'Enrollment_Fee', '0.00'),
                'Enrollment_Fee': getattr(self, 'EnrollmentFee', None) or getattr(self, 'Enrollment_Fee', '0.00'),
                'quote_request_timestamp': self.quote_request_timestamp,
                'plan_name_for_img': self.Name.lower().replace(' ', '-')}

        self.actual_premium = decimal.Decimal(data['Premium'])

        if self.Name == 'Principle Advantage':
            data.update({'TelaDocFee': self.TelaDocFee,
                         'TelaDoc_Fee': self.TelaDocFee})
            self.actual_premium += decimal.Decimal(data['TelaDocFee'])

        if self.Name == 'Cardinal Choice':
            data.update({
                'TelaDoc_Fee': getattr(self, 'TelaDoc_Fee', '0.00'),
                'TelaDocFee': getattr(self, 'TelaDoc_Fee', '0.00'),
                'RxAdvocacy_Fee': getattr(self, 'RxAdvocacy_Fee', '0.00'),
                'RxAdvocacyFee': getattr(self, 'RxAdvocacy_Fee', '0.00'),
                'ChoiceValue_AdminFee': getattr(self, 'ChoiceValue_AdminFee', '0.00'),
                'ChoiceValueSavings_Fee': getattr(self, 'ChoiceValueSavings_Fee', '0.00'),
                'RealValueSavings_Fee': getattr(self, 'RealValueSavings_Fee', '0.00'),
                'RealValueSavings_AdminFee': getattr(self, 'RealValueSavings_AdminFee', '0.00'),
            })
            self.actual_premium += (decimal.Decimal(data['TelaDocFee']) +
                                    decimal.Decimal(data['RxAdvocacy_Fee']) +
                                    decimal.Decimal(data['ChoiceValue_AdminFee']) +
                                    decimal.Decimal(data['ChoiceValueSavings_Fee']) +
                                    decimal.Decimal(data['RealValueSavings_Fee']) +
                                    decimal.Decimal(data['RealValueSavings_AdminFee']))

        if self.Name == 'Unified Health One':
            data.update({'AdministrativeFee': self.AdministrativeFee,
                         'Administrative_Fee': self.AdministrativeFee})
            self.actual_premium += decimal.Decimal(data['AdministrativeFee'])


        if self.Name == 'Vitala Care':
            data.update({
                'TelaDoc_Fee': getattr(self, 'TelaDoc_Fee', '0.00'),
                'TelaDocFee': getattr(self, 'TelaDoc_Fee', '0.00'),
                'RxAdvocacy_Fee': getattr(self, 'RxAdvocacy_Fee', '0.00'),
                'RxAdvocacyFee': getattr(self, 'RxAdvocacy_Fee', '0.00'),
                'ChoiceValue_AdminFee': getattr(self, 'ChoiceValue_AdminFee', '0.00'),
                'ChoiceValueSavings_Fee': getattr(self, 'ChoiceValueSavings_Fee', '0.00'),
            })
            self.actual_premium += (decimal.Decimal(data['TelaDocFee']) +
                                    decimal.Decimal(data['RxAdvocacy_Fee']) +
                                    decimal.Decimal(data['ChoiceValue_AdminFee']) +
                                    decimal.Decimal(data['ChoiceValueSavings_Fee']))

        if self.Name == 'Health Choice':
            data.update({
                'TelaDoc_Fee': getattr(self, 'TelaDoc_Fee', '0.00'),
                'TelaDocFee': getattr(self, 'TelaDoc_Fee', '0.00'),
                'RxAdvocacy_Fee': getattr(self, 'RxAdvocacy_Fee', '0.00'),
                'RxAdvocacyFee': getattr(self, 'RxAdvocacy_Fee', '0.00'),
                'ChoiceValue_AdminFee': getattr(self, 'ChoiceValue_AdminFee', '0.00'),
                'ChoiceValueSavings_Fee': getattr(self, 'ChoiceValueSavings_Fee', '0.00'),
            })
            self.actual_premium += (decimal.Decimal(data['TelaDocFee']) +
                                    decimal.Decimal(data['RxAdvocacy_Fee']) +
                                    decimal.Decimal(data['ChoiceValue_AdminFee']) +
                                    decimal.Decimal(data['ChoiceValueSavings_Fee']))

        if self.Name == 'Legion Limited Medical':
            data.update({
                'TelaDoc_Fee': getattr(self, 'TelaDoc_Fee', '0.00'),
                'TelaDocFee': getattr(self, 'TelaDoc_Fee', '0.00'),
                'RxAdvocacy_Fee': getattr(self, 'RxAdvocacy_Fee', '0.00'),
                'RxAdvocacyFee': getattr(self, 'RxAdvocacy_Fee', '0.00'),
                'ChoiceValue_AdminFee': getattr(self, 'ChoiceValue_AdminFee', '0.00'),
                'ChoiceValueSavings_Fee': getattr(self, 'ChoiceValueSavings_Fee', '0.00'),
            })
            self.actual_premium += (decimal.Decimal(data['TelaDocFee']) +
                                    decimal.Decimal(data['RxAdvocacy_Fee']) +
                                    decimal.Decimal(data['ChoiceValue_AdminFee']) +
                                    decimal.Decimal(data['ChoiceValueSavings_Fee']))

        # For standalone ancillaries

        if self.Name in copy.deepcopy(settings.TYPEWISE_PLAN_LIST['anc']):
            self.Ins_Type = 'anc'
            self.stand_alone_addon_plan = True

            data.update({
                'ins_type': self.Ins_Type,
                'stand_alone_addon_plan': self.stand_alone_addon_plan
            })

            if self.Name == 'USA Dental':
                data.update({
                    'Enrollment_Fee': getattr(self, 'EnrollmentFee', '0.00'),
                    'EnrollmentFee': getattr(self, 'EnrollmentFee', '0.00'),
                    'note': getattr(self, 'note', None)
                })

            if self.Name == 'Safeguard Critical Illness':
                data.update({
                    'AdministrativeFee': getattr(self, 'AdministrativeFee', '0.00'),
                    'Administrative_Fee': getattr(self, 'AdministrativeFee', '0.00'),
                })
                self.actual_premium += (decimal.Decimal(data['AdministrativeFee']))

            if self.Name == 'Freedom Spirit Plus':
                data.update({
                    'AdministrativeFee': getattr(self, 'AdministrativeFee', '0.00'),
                    'Administrative_Fee': getattr(self, 'AdministrativeFee', '0.00'),
                    'Enrollment_Fee': getattr(self, 'EnrollmentFee', '0.00'),
                    'EnrollmentFee': getattr(self, 'EnrollmentFee', '0.00'),
                })
                self.actual_premium += (decimal.Decimal(data['AdministrativeFee']))


        data['actual_premium'] = str(self.actual_premium)
        return data


class StmQuoteResponse(object):
    special_tags = ['Quote_ID', 'Access_Token', 'PolicyNote']

    def __init__(self, stm_name, xml_text, state, ZipCode=None):
        self.stm_name = stm_name
        self.ZipCode = ZipCode
        self.State = state
        self.xml_text = xml_text
        self.escaped_xml_text = xml_text.replace('&', '&amp;').replace('"', '&quot;').replace("'", '&#39;')
        # MEMORY_EXHAUSTIVE print("STM QUOTE RESPONSE FOR {1}: {0}".format(self.escaped_xml_text, self.stm_name))
        self.root = ET.fromstring(self.escaped_xml_text)

        self.Quote_ID = None

        self.Quote_ID = (self.root.find('Quote_ID').text
                         if isinstance(self.root.find('Quote_ID'), ET.Element) else None)
        if self.Quote_ID is None:
            self.Quote_ID = (self.root.find('Quote').text
                             if isinstance(self.root.find('Quote'), ET.Element) else None)

        self.Access_Token = (self.root.find('Access_Token').text
                             if isinstance(self.root.find('Access_Token'), ET.Element) else None)
        self.PolicyNote = (self.root.find('PolicyNote').text
                           if isinstance(self.root.find('PolicyNote'), ET.Element) else None)

        self.monthly = []
        self.addon_plans = []
        self.errors = []

        self.process()

    def process(self):
        processors = {
            'SixMonth': self.process_month_six,
            'ThreeMonth': self.process_three_month,
            'ElevenMonth': self.process_month_eleven,
            'TwelveMonth': self.process_month_twelve,
            'Add-ons': self.process_addon,
            'Error': self.process_error
        }
        for child in self.root:
            try:
                processors[child.tag.replace("_", '')](child)
            except KeyError:
                if child.tag not in self.special_tags:
                    self.process_month(getattr(self, 'Duration_Coverage', 10), self.root)

    def process_month_six(self, month_tree):
        self.process_month(6, month_tree)

    def process_three_month(self, month_tree):
        self.process_month(3, month_tree)

    def process_month_eleven(self, month_tree):
        self.process_month(11, month_tree)

    def process_month_twelve(self, month_tree):
        self.process_month(12, month_tree)

    def process_month(self, month, month_tree):
        raise NotImplemented

    def process_addon(self, addons_tree):
        for child in addons_tree:
            match = ADDON_ID_PATTERN.match(child.tag)
            if match:
                self.process_addon_id(match.groupdict()['addon_id'], child)

    def process_addon_id(self, addon_id, addon_id_tree):
        for child in addon_id_tree:
            self.process_addon_plan(addon_id, child)

    def process_addon_plan(self, addon_id, plan_tree):
        plan = AddonPlan(self.stm_name, addon_id, plan_tree=plan_tree)
        plan.quote_response = self
        self.addon_plans.append(plan)

    def process_policy_note(self, policy_note_tree):
        pass

    def process_error(self, error_tree):
        error_message = error_tree.find('Message').text if isinstance(error_tree.find('Message'), ET.Element) else ''
        self.errors = error_message.strip().split('#')

    def is_valid(self):
        return (self.Quote_ID is not None) and (self.Access_Token is not None) and not self.errors


class AddonPlan(object):

    def __init__(self, stm_name, addon_id, Name=None, carrier_name=None,
                 carrier_id=None, Premium=None, plan_tree=None, *args, **kwargs):
        self.stm_name = stm_name
        self.addon_id = str(addon_id)
        self.Name = Name
        self.carrier_name = carrier_name or add_on_properties.get(self.addon_id, {"name": None})["name"]
        self.carrier_id = carrier_id or add_on_carrier_id.get(self.carrier_name, "0")
        self.Premium = Premium

        self.plan_tree = plan_tree
        self.quote_response = None

        for key, value in kwargs.items():
            setattr(self, key, value)

        if self.plan_tree is not None:
            self.process()

    @property
    def actual_premium(self):
        return str(decimal.Decimal(self.Premium) +
                   decimal.Decimal(self.AdministrativeFee) +
                   decimal.Decimal(self.MedsenseFee))

    @actual_premium.setter
    def actual_premium(self, value):
        pass

    def process(self):
        self.d = [('addon_id', self.addon_id)]
        for child in self.plan_tree:
            self.d.append((child.tag, html.unescape(child.text)))
            setattr(self, child.tag, html.unescape(child.text))

    def plan_name(self):
        return self.Name

    def data_as_dict(self):
        data = dict(
            stm_name=self.stm_name,
            addon_id=self.addon_id,
            Name=self.Name,
            carrier_name=self.carrier_name,
            carrier_id=self.carrier_id,
            Premium=self.Premium,
            AdministrativeFee=self.AdministrativeFee,
            EnrollmentFee=self.EnrollmentFee,
            MedsenseFee=self.MedsenseFee,
            Embeded=self.Embeded,
            actual_premium=self.actual_premium,
        )
        if int(self.addon_id) == 38:
            data.update({
                'Plan': self.Plan,
                'Plan_Code': self.Plan_Code,
                'Deductible': self.Deductible,
            })
        return data

    def __hash__(self):
        return hash((str(self.stm_name), str(self.addon_id), str(self.Name), str(self.Premium)))

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and self.addon_id == other.addon_id and
                self.Name == other.Name and self.Premium == other.Premium and self.stm_name == other.stm_name)

    def __str__(self):
        return "(smt_name: {0}, addon_id: {1}, name: {2}, 'premium': {3})".format(self.stm_name, self.addon_id,
                                                                                  self.Name, self.Premium)

    def __repr__(self):
        return self.__str__()


class StmPlan(object):

    def __init__(self, stm_name, state, month, option, **kwargs):
        self.month = month
        self.State = state
        self.option = option

        self.Name = stm_name
        self.Duration_Coverage = None
        self.quote_request_timestamp = None

        self.Premium = None
        self.Coinsurance_Percentage = None
        self.actual_premium = None

        self.Quote_ID = None
        self.Access_Token = None

        self.Ins_Type = 'stm'

        for k, v in kwargs.items():
            setattr(self, k, v)

    def __str__(self):
        return "<Month: {0}~~{1}@@{2}>".format(self.Name, self.option, self.month)

    def get_general_plan_name(self):
        plan_name = "{0} {1}@{2}".format(self.Name, self.option, self.Duration_Coverage)
        if self.Name in ['Everest STM', 'LifeShield STM', 'AdvantHealth STM']:
            return plan_name + ' Plan {0}'.format(self.Plan)
        return plan_name

    def get_plan_name(self):
        plan_name = "{0} {1}/{2}/{3}/{4}@{5}".format(self.Name, self.option, self.get_out_of_pocket(),
                                                     self.get_coverage_max(), self.Coinsurance_Percentage,
                                                     self.Duration_Coverage)

        return plan_name

    def get_unique_url(self):
        unique_url = "{0}-{1}-{2}-{3}-{4}-{5}-{6}".format(self.Name.replace(' ', '_'), self.State.lower(),
                                                          self.option, self.get_out_of_pocket(),
                                                          self.get_coverage_max(), self.Coinsurance_Percentage,
                                                          self.Duration_Coverage)
        if self.Name in ['Everest STM', 'LifeShield STM', 'AdvantHealth STM']:
            return unique_url + 'p{0}'.format(self.Plan)
        return unique_url

    # 270119: Shortened plan url by removing get_out_of_pocket, coverage_max, Coinsurance_Percentage
    def get_general_url(self):
        general_url = "{0}-{1}-{2}-{3}".format(self.Name.replace(' ', '_'), self.State.lower(),
                                                          self.option,
                                                          self.Duration_Coverage)
        if self.Name in ['Everest STM', 'LifeShield STM', 'AdvantHealth STM']:
            return general_url + 'p{0}'.format(self.Plan)
        return general_url

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.get_general_url() == other.get_general_url()

    def __hash__(self):
        return hash("Insurance_Package:{0}_{1}".format(self.__class__.__name__, self.get_general_url))

    def get_out_of_pocket(self):
        """
        For Premier STM 'Out_Of_Pocket'
        For Everest STM 'Benefit_Amount'
        Others 'Coinsurance_Limit'
        """
        return getattr(self, 'Coinsurance_Limit', getattr(self, 'Out_Of_Pocket', getattr(self, 'Benefit_Amount', None)))

    def get_coverage_max(self):
        return getattr(self, 'Coverage_Max', getattr(self, 'Benefit_Amount', None))

    def get_data_as_dict(self):
        data = {'Name': self.Name, 'month': self.month, 'option': self.option,
                'Coinsurance_Percentage': self.Coinsurance_Percentage, 'Premium': self.Premium,
                'unique_url': self.get_unique_url(), 'general_url': self.get_general_url(),
                'plan_name': self.get_plan_name(), 'general_plan_name': self.get_general_plan_name(),
                'out_of_pocket_value': self.get_out_of_pocket(), 'coverage_max_value': self.get_coverage_max(),
                'Quote_ID': self.Quote_ID, 'Access_Token': self.Access_Token, 'Plan_ID': self.Plan_ID,
                'Duration_Coverage': self.Duration_Coverage, 'quote_request_timestamp': self.quote_request_timestamp,
                'copay': self.copay, 'copay_text': self.copay_text, 'ins_type': self.Ins_Type,
                'plan_name_for_img': self.Name.lower().replace(' ', '-')}

        self.actual_premium = decimal.Decimal(data['Premium'])

        if self.Name == 'HealtheFlex STM' or self.Name == 'HealtheMed STM' or self.Name == 'Sage STM':
            data.update({'Coinsurance_Limit': self.Coinsurance_Limit, 'AdministrativeFee': self.AdministrativeFee,
                         'Administrative_Fee': self.AdministrativeFee, 'EnrollmentFee': self.EnrollmentFee,
                         'Enrollment_Fee': self.EnrollmentFee, 'Note': self.Note,
                         'Payment_Option': self.Payment_Option})
            self.actual_premium += decimal.Decimal(data['Administrative_Fee'])

        if self.Name == 'HealtheFlex STM' or self.Name == 'HealtheMed STM':
            data.update({'Deductible_Option': '${0:,}'.format(int(self.option))})
            if data['Duration_Coverage'] == '':
                data['Duration_Coverage'] = data['month']

        if self.Name == 'Sage STM':
            data.update({'Deductible_Option': 'Option{0}'.format(int(self.option)),
                         'copay_2': self.copay_2, 'copay_2_text': self.copay_2_text})

        if self.Name == 'Premier STM':
            data.update({'Benefit_Amount': self.Benefit_Amount, 'Out_Of_Pocket': self.Out_Of_Pocket,
                         'AdministrativeFee': self.AdministrativeFee, 'EnrollmentFee': self.EnrollmentFee,
                         'GapAffordPlus_Fee': self.GapAffordPlus_Fee, 'Note': self.Note,
                         'GapAffordPlus_AdminFee': self.GapAffordPlus_AdminFee,
                         'Deductible_Option': 'Option{0}'.format(self.option), 'Enrollment_Fee': self.EnrollmentFee,
                         'Administrative_Fee': self.AdministrativeFee})
            self.actual_premium += (decimal.Decimal(data['Administrative_Fee']) +
                                    decimal.Decimal(data['GapAffordPlus_Fee']) +
                                    decimal.Decimal(data['GapAffordPlus_AdminFee']))

        if self.Name == 'Everest STM':
            data.update({'Plan': self.Plan,
                         'ChoiceValueSavings_Fee': getattr(self, 'ChoiceValueSavings_Fee', '0.00'),
                         'ChoiceValue_AdminFee': getattr(self, 'ChoiceValue_AdminFee', '0.00'),
                         'VBP_Fee': getattr(self, 'VBP_Fee', '0.00'),
                         'TelaDoc_Fee': getattr(self, 'TelaDoc_Fee', '0.00'),
                         'Medsense_Fee': getattr(self, 'Medsense_Fee', '0.00'),
                         'RxAdvocacy_Fee': getattr(self, 'RxAdvocacy_Fee', '0.00'),
                         'Enrollment_Fee': getattr(self, 'Enrollment_Fee', '0.00'),
                         'Payment_Option': self.Payment_Option,
                         'Plan_Name': 'Plan {0}'.format(self.Plan),
                         'Coverage_Max': self.get_coverage_max(),
                         'Benefit_Amount': self.get_out_of_pocket(),
                         'Deductible_Option': 'Option{0}'.format(int(self.option)),
                         'EnrollmentFee': getattr(self, 'Enrollment_Fee', '0.00'),
                         'copay_2': self.copay_2,
                         'copay_2_text': self.copay_2_text})
            self.actual_premium += (decimal.Decimal(data['RxAdvocacy_Fee']) +
                                    decimal.Decimal(data['Medsense_Fee']) +
                                    decimal.Decimal(data['TelaDoc_Fee']) +
                                    decimal.Decimal(data.get('ChoiceValueSavings_Fee', '0.0')) +
                                    decimal.Decimal(data.get('ChoiceValue_AdminFee', '0.00')) +
                                    decimal.Decimal(data.get('VBP_Fee', '0.00')))

        if self.Name == 'Select STM':
            data.update({'Plan': self.Plan, 'ChoiceValueSavings_Fee': getattr(self, 'ChoiceValueSavings_Fee', '0.00'),
                         'ChoiceValue_AdminFee': getattr(self, 'ChoiceValue_AdminFee', '0.00'),
                         'VBP_Fee': getattr(self, 'VBP_Fee', '0.00'),
                         'TelaDoc_Fee': getattr(self, 'TelaDoc_Fee', '0.00'),
                         'Medsense_Fee': getattr(self, 'Medsense_Fee', '0.00'),
                         'RxAdvocacy_Fee': getattr(self, 'RxAdvocacy_Fee', '0.00'),
                         'Enrollment_Fee': getattr(self, 'Enrollment_Fee', '0.00'),
                         'Payment_Option': self.Payment_Option,
                         'Plan_Name': 'Plan {0}'.format(self.Plan),
                         'Coverage_Max': self.get_coverage_max(),
                         'Policy_Max': self.get_coverage_max(),
                         'Benefit_Amount': self.get_out_of_pocket(),
                         'Deductible_Option': 'Option{0}'.format(int(self.option)),
                         'EnrollmentFee': self.Enrollment_Fee, 'copay_2': self.copay_2,
                         'copay_2_text': self.copay_2_text})
            self.actual_premium += (decimal.Decimal(data['RxAdvocacy_Fee']) +
                                    decimal.Decimal(data['Medsense_Fee']) +
                                    decimal.Decimal(data['TelaDoc_Fee']) +
                                    decimal.Decimal(data.get('ChoiceValueSavings_Fee', '0.0')) +
                                    decimal.Decimal(data.get('ChoiceValue_AdminFee', '0.00')) +
                                    decimal.Decimal(data.get('VBP_Fee', '0.00')))

        if self.Name == 'LifeShield STM':
            data.update({'Plan': self.Plan, 'ChoiceValueSavings_Fee': getattr(self, 'ChoiceValueSavings_Fee', '0.00'),
                         'ChoiceValue_AdminFee': getattr(self, 'ChoiceValue_AdminFee', '0.00'),
                         'RealValueSavings_Fee': getattr(self, 'RealValueSavings_Fee', '0.00'),
                         'RealValueSavings_AdminFee': getattr(self, 'RealValueSavings_AdminFee', '0.00'),
                         'VBP_Fee': getattr(self, 'VBP_Fee', '0.00'),
                         'TelaDoc_Fee': self.TelaDoc_Fee,
                         'Medsense_Fee': getattr(self, 'Medsense_Fee', '0.00'),
                         'RxAdvocacy_Fee': self.RxAdvocacy_Fee, 'Enrollment_Fee': self.Enrollment_Fee,
                         'Payment_Option': self.Payment_Option, 'Plan_Name': 'Plan {0}'.format(self.Plan),
                         'Coverage_Max': self.get_coverage_max(), 'Benefit_Amount': self.get_out_of_pocket(),
                         'Deductible_Option': 'Option{0}'.format(int(self.option)),
                         'EnrollmentFee': self.Enrollment_Fee, 'copay_2': self.copay_2,
                         'copay_2_text': self.copay_2_text})
            self.actual_premium += (decimal.Decimal(data['RxAdvocacy_Fee']) +
                                    decimal.Decimal(data['Medsense_Fee']) +
                                    decimal.Decimal(data['TelaDoc_Fee']) +
                                    decimal.Decimal(data.get('RealValueSavings_Fee', '0.0')) +
                                    decimal.Decimal(data.get('RealValueSavings_AdminFee', '0.00')) +
                                    decimal.Decimal(data.get('ChoiceValueSavings_Fee', '0.0')) +
                                    decimal.Decimal(data.get('ChoiceValue_AdminFee', '0.00')) +
                                    decimal.Decimal(data.get('VBP_Fee', '0.00')))

        if self.Name == 'AdvantHealth STM':
            data.update({'Plan': self.Plan, 'ChoiceValueSavings_Fee': getattr(self, 'ChoiceValueSavings_Fee', '0.00'),
                         'ChoiceValue_AdminFee': getattr(self, 'ChoiceValue_AdminFee', '0.00'),
                         'RealValueSavings_Fee': getattr(self, 'RealValueSavings_Fee', '0.00'),
                         'RealValueSavings_AdminFee': getattr(self, 'RealValueSavings_AdminFee', '0.00'),
                         'Association_Fee': getattr(self, 'Association_Fee', '0.00'),
                         'VBP_Fee': getattr(self, 'VBP_Fee', '0.00'),
                         'TelaDoc_Fee': self.TelaDoc_Fee,
                         'Medsense_Fee': getattr(self, 'Medsense_Fee', '0.00'),
                         'RxAdvocacy_Fee': self.RxAdvocacy_Fee, 'Enrollment_Fee': self.Enrollment_Fee,
                         'Payment_Option': self.Payment_Option, 'Plan_Name': 'Plan {0}'.format(self.Plan),
                         'Coverage_Max': self.get_coverage_max(), 'Benefit_Amount': self.get_out_of_pocket(),
                         'Deductible_Option': 'Option{0}'.format(int(self.option)),
                         'EnrollmentFee': self.Enrollment_Fee, 'copay_2': self.copay_2,
                         'copay_2_text': self.copay_2_text})
            self.actual_premium += (decimal.Decimal(data['RxAdvocacy_Fee']) +
                                    decimal.Decimal(data['Medsense_Fee']) +
                                    decimal.Decimal(data['TelaDoc_Fee']) +
                                    decimal.Decimal(data['Association_Fee']) +
                                    decimal.Decimal(data.get('RealValueSavings_Fee', '0.0')) +
                                    decimal.Decimal(data.get('RealValueSavings_AdminFee', '0.00')) +
                                    decimal.Decimal(data.get('ChoiceValueSavings_Fee', '0.0')) +
                                    decimal.Decimal(data.get('ChoiceValue_AdminFee', '0.00')) +
                                    decimal.Decimal(data.get('VBP_Fee', '0.00')))


        data['actual_premium'] = str(self.actual_premium)
        return data

    def __repr__(self):
        return self.__str__()


class LifeShieldResponse(StmQuoteResponse):

    special_tags = ['Quote', 'Access_Token', 'PolicyNote']

    def __init__(self, stm_name, xml_text, state, coinsurance_percentage, benefit_amount,
                 coverage_max, quote_request_timestamp, Duration_Coverage, Plan_ID,
                 Payment_Option, request_data_combination):
        self.Coinsurance_Percentage = coinsurance_percentage
        self.Benefit_Amount = benefit_amount
        self.Coverage_Max = coverage_max
        self.Duration_Coverage = Duration_Coverage
        self.quote_request_timestamp = quote_request_timestamp
        self.Plan_ID = Plan_ID
        self.Payment_Option = Payment_Option
        self.request_data_combination = request_data_combination
        super(LifeShieldResponse, self).__init__(stm_name, xml_text, state)

    def process_month(self, month, month_tree):
        attrs = {'Coinsurance_Percentage': self.Coinsurance_Percentage,
                 'Benefit_Amount': self.Benefit_Amount,
                 'Coverage_Max': self.Coverage_Max,
                 'Quote_ID': self.Quote_ID,
                 'Plan_ID': self.Plan_ID,
                 'Access_Token': self.Access_Token,
                 'Duration_Coverage': self.Duration_Coverage,
                 'quote_request_timestamp': self.quote_request_timestamp,
                 'Payment_Option': self.Payment_Option,
                 'copay': '50',
                 'copay_text': '',
                 'copay_2': '50',
                 'copay_2_text': ''}
        options = []
        for plan in month_tree:
            try:
                plan_no = plan.tag.split('_')[1]
            except IndexError as err:
                print("LifeShield.process_month: {0}".format(err))
            for option in plan:
                match = MONTH_OPTION_PATTERN.match(option.tag)
                if match:
                    mv = match.groupdict()
                    for prop in option:
                        mv[prop.tag] = prop.text
                    mv['Plan'] = plan_no
                    options.append(mv)
        for opt in options:
            opt.update(attrs)
            stm_plan = StmPlan(self.stm_name, self.State, month, **opt)
            if stm_plan not in self.monthly:
                self.monthly.append(stm_plan)


class AdvantHealthResponse(StmQuoteResponse):

    special_tags = ['Quote', 'Access_Token', 'PolicyNote']

    def __init__(self, stm_name, xml_text, state, coinsurance_percentage, benefit_amount,
                 coverage_max, quote_request_timestamp, Duration_Coverage, Plan_ID,
                 Payment_Option, request_data_combination):
        self.Coinsurance_Percentage = coinsurance_percentage
        self.Benefit_Amount = benefit_amount
        self.Coverage_Max = coverage_max
        self.Duration_Coverage = Duration_Coverage
        self.quote_request_timestamp = quote_request_timestamp
        self.Plan_ID = Plan_ID
        self.Payment_Option = Payment_Option
        self.request_data_combination = request_data_combination
        super(AdvantHealthResponse, self).__init__(stm_name, xml_text, state)

    def process_month(self, month, month_tree):
        attrs = {'Coinsurance_Percentage': self.Coinsurance_Percentage,
                 'Benefit_Amount': self.Benefit_Amount,
                 'Coverage_Max': self.Coverage_Max,
                 'Quote_ID': self.Quote_ID,
                 'Plan_ID': self.Plan_ID,
                 'Access_Token': self.Access_Token,
                 'Duration_Coverage': self.Duration_Coverage,
                 'quote_request_timestamp': self.quote_request_timestamp,
                 'Payment_Option': self.Payment_Option,
                 'copay': '50',
                 'copay_text': '',
                 'copay_2': '50',
                 'copay_2_text': ''}
        options = []
        for plan in month_tree:
            try:
                plan_no = plan.tag.split('_')[1]
            except IndexError as err:
                print(f'AdvantHealth.process_month: {err}')
            for option in plan:
                match = MONTH_OPTION_PATTERN.match(option.tag)
                if match:
                    mv = match.groupdict()
                    for prop in option:
                        mv[prop.tag] = prop.text
                    mv['Plan'] = plan_no
                    options.append(mv)
        for opt in options:
            opt.update(attrs)
            stm_plan = StmPlan(self.stm_name, self.State, month, **opt)
            if stm_plan not in self.monthly:
                self.monthly.append(stm_plan)


class EverestResponse(StmQuoteResponse):
    """
    Monthly Plan
    ============
        Name - string

        Coinsurance_Percentage - int
        Benefit_Amount - int
        Coverage_Max - int

        Plan - int

        Premium - decimal
        ChoiceValueSavings_Fee - decimal
        TelaDoc_Fee - decimal
        Medsense_Fee - decimal
        RxAdvocacy_Fee - decimal
        Enrollment_Fee - decimal


    Add Ons Plan
    ============
        Name - string
        Premium - decimal
        AdministrativeFee - decimal
        EnrollmentFee - decimal
        MedsenseFee - decimal
        Embeded - string [Yes/No]
    """
    special_tags = ['Quote', 'Access_Token', 'PolicyNote']

    copay = {
        '1': {'copay': '30', 'copay_text': 'Office Visit Copay'},
        '2': {'copay': '50', 'copay_text': 'Office Visit Copay'},
        '3': {'copay': '40', 'copay_text': 'Office Visit Copay'},
    }
    
    def __init__(self, stm_name, xml_text, state, coinsurance_percentage, benefit_amount,
                 coverage_max, quote_request_timestamp, Duration_Coverage, Plan_ID,
                 Payment_Option, request_data_combination):
        self.Coinsurance_Percentage = coinsurance_percentage
        self.Benefit_Amount = benefit_amount
        self.Coverage_Max = coverage_max
        self.Duration_Coverage = Duration_Coverage
        self.quote_request_timestamp = quote_request_timestamp
        self.Plan_ID = Plan_ID
        self.Payment_Option = Payment_Option
        self.request_data_combination = request_data_combination
        print("EverestResponse->(Duration_Coverage): ", self.Duration_Coverage)
        super().__init__(stm_name, xml_text, state)

    def process_month(self, month, month_tree):
        attrs = {'Coinsurance_Percentage': self.Coinsurance_Percentage,
                 'Benefit_Amount': self.Benefit_Amount,
                 'Coverage_Max': self.Coverage_Max,
                 'Quote_ID': self.Quote_ID,
                 'Plan_ID': self.Plan_ID,
                 'Access_Token': self.Access_Token,
                 'Duration_Coverage': self.Duration_Coverage,
                 'quote_request_timestamp': self.quote_request_timestamp,
                 'Payment_Option': self.Payment_Option,
                 'copay': '50',
                 'copay_text': 'Office Visit Copay',
                 'copay_2': '50',
                 'copay_2_text': 'Urgent Care Copay'}
        options = []
        for plan in month_tree:
            try:
                plan_no = plan.tag.split('_')[1]
            except IndexError as err:
                print("EverestResponse.process_month: {0}".format(err))
            for option in plan:
                match = MONTH_OPTION_PATTERN.match(option.tag)
                if match:
                    mv = match.groupdict()
                    for prop in option:
                        mv[prop.tag] = prop.text
                    mv['Plan'] = plan_no
                    options.append(mv)
        for opt in options:
            copay_info = self.copay.get(str(opt['Plan']))
            if copay_info:
                attrs['copay'] = copay_info['copay']
                attrs['copay_text'] = copay_info['copay_text']
            opt.update(attrs)
            stm_plan = StmPlan(self.stm_name, self.State, month, **opt)
            if stm_plan not in self.monthly:
                self.monthly.append(stm_plan)


class SelectResponse(StmQuoteResponse):
    """
    Monthly Plan
    ============
        Name - string

        Coinsurance_Percentage - int
        Benefit_Amount - int
        Coverage_Max - int

        Plan - int

        Premium - decimal
        ChoiceValueSavings_Fee - decimal
        TelaDoc_Fee - decimal
        Medsense_Fee - decimal
        RxAdvocacy_Fee - decimal
        Enrollment_Fee - decimal


    Add Ons Plan
    ============
        Name - string
        Premium - decimal
        AdministrativeFee - decimal
        EnrollmentFee - decimal
        MedsenseFee - decimal
        Embeded - string [Yes/No]
    """
    special_tags = ['Quote', 'Access_Token', 'PolicyNote']

    copay = {
        '1': {'copay': '30', 'copay_text': 'Office Visit Copay'},
        '2': {'copay': '50', 'copay_text': 'Office Visit Copay'},
        '3': {'copay': '40', 'copay_text': 'Office Visit Copay'},
    }

    def __init__(self, stm_name, xml_text, state, coinsurance_percentage, benefit_amount,
                 coverage_max, quote_request_timestamp, Duration_Coverage, Plan_ID,
                 Payment_Option, request_data_combination):
        self.Coinsurance_Percentage = coinsurance_percentage
        self.Benefit_Amount = benefit_amount
        self.Coverage_Max = coverage_max
        self.Policy_Max = coverage_max
        self.Duration_Coverage = Duration_Coverage
        self.quote_request_timestamp = quote_request_timestamp
        self.Plan_ID = Plan_ID
        self.Payment_Option = Payment_Option
        self.request_data_combination = request_data_combination
        print("SelectResponse->(Duration_Coverage): ", self.Duration_Coverage)
        super().__init__(stm_name, xml_text, state)

    def process_month(self, month, month_tree):
        attrs = {'Coinsurance_Percentage': self.Coinsurance_Percentage,
                 'Benefit_Amount': self.Benefit_Amount,
                 'Coverage_Max': self.Coverage_Max,
                 'Policy_Max': self.Policy_Max,
                 'Quote_ID': self.Quote_ID,
                 'Plan_ID': self.Plan_ID,
                 'Access_Token': self.Access_Token,
                 'Duration_Coverage': self.Duration_Coverage,
                 'quote_request_timestamp': self.quote_request_timestamp,
                 'Payment_Option': self.Payment_Option,
                 'copay': '50',
                 'copay_text': 'Office Visit Copay',
                 'copay_2': '50',
                 'copay_2_text': 'Urgent Care Copay'}
        options = []
        for plan in month_tree:
            try:
                plan_no = plan.tag.split('_')[1]
            except IndexError as err:
                print("EverestResponse.process_month: {0}".format(err))
            for option in plan:
                match = MONTH_OPTION_PATTERN.match(option.tag)
                if match:
                    mv = match.groupdict()
                    for prop in option:
                        mv[prop.tag] = prop.text
                    mv['Plan'] = plan_no
                    options.append(mv)
        for opt in options:
            copay_info = self.copay.get(str(opt['Plan']))
            if copay_info:
                attrs['copay'] = copay_info['copay']
                attrs['copay_text'] = copay_info['copay_text']
            opt.update(attrs)
            stm_plan = StmPlan(self.stm_name, self.State, month, **opt)
            if stm_plan not in self.monthly:
                self.monthly.append(stm_plan)


class HealtheFlexResponse(StmQuoteResponse):
    """
    Monthly Plan
    ============
        Name - string

        Coinsurance_Limit - int
        Coinsurance_Percentage - int
        Coverage_Max - int

        Premium - decimal
        AdministrativeFee - decimal
        EnrollmentFee - decimal
        Note - string


    Add Ons Plan
    ============
        Name - string
        Premium - decimal
        AdministrativeFee - decimal
        EnrollmentFee - decimal
        MedsenseFee - decimal
        Embeded - string [Yes/No]
    """

    def __init__(self, stm_name, xml_text, state, coinsurance_percentage, coinsurance_limit,
                 coverage_max, quote_request_timestamp, Duration_Coverage, Plan_ID, Payment_Option, ZipCode=None):
        self.Coinsurance_Percentage = coinsurance_percentage
        self.Coinsurance_Limit = coinsurance_limit
        self.Coverage_Max = coverage_max
        self.Duration_Coverage = Duration_Coverage
        self.quote_request_timestamp = quote_request_timestamp
        self.Plan_ID = Plan_ID
        self.Payment_Option = Payment_Option
        super().__init__(stm_name, xml_text, state, ZipCode)

    def process_month(self, month, month_tree):
        attrs = {'Coinsurance_Percentage': self.Coinsurance_Percentage,
                 'Coinsurance_Limit': self.Coinsurance_Limit,
                 'Coverage_Max': self.Coverage_Max,
                 'Quote_ID': self.Quote_ID,
                 'Plan_ID': self.Plan_ID,
                 'Access_Token': self.Access_Token,
                 'Duration_Coverage': self.Duration_Coverage,
                 'quote_request_timestamp': self.quote_request_timestamp,
                 'Payment_Option': self.Payment_Option,
                 'copay': '50',
                 'copay_text': 'Urgent Care Copay'}
        options = []
        for child in month_tree:
            match = MONTH_OPTION_PATTERN.match(child.tag)
            if match:
                mv = match.groupdict()
                mv.update({'Premium': child.text})
                options.append(mv)
            else:
                attrs[child.tag] = html.unescape(child.text)
        for opt in options:
            opt.update(attrs)
            self.monthly.append(StmPlan(self.stm_name, self.State, month, **opt))


class HealtheMedResponse(HealtheFlexResponse):
    """
    Monthly Plan
    ============
        Name - string

        Coinsurance_Limit - decimal
        Coinsurance_Percentage - int
        Coverage_Max - int

        Premium - decimal
        AdministrativeFee - decimal
        EnrollmentFee - decimal
        Note - string


    Add Ons Plan
    ============
        Name - string
        Premium - decimal
        AdministrativeFee - decimal
        EnrollmentFee - decimal
        MedsenseFee - decimal
        Embeded - string [Yes/No]
    """


class SageResponse(StmQuoteResponse):
    """
    Monthly Plan
    ============
        Name - string

        Coinsurance_Limit - int
        Coinsurance_Percentage - int
        Coverage_Max - int

        Premium - decimal
        AdministrativeFee - decimal
        EnrollmentFee - decimal
        Note - string


    Add Ons Plan
    ============
        Name - string
        Premium - decimal
        AdministrativeFee - decimal
        EnrollmentFee - decimal
        MedsenseFee - decimal
        Embeded - string [Yes/No]
    """
    special_tags = ['Quote', 'Access_Token', 'PolicyNote']

    def __init__(self, stm_name, xml_text, state, coinsurance_percentage,
                 quote_request_timestamp, Duration_Coverage, Plan_ID,
                 Payment_Option, request_data_combination):
        self.Coinsurance_Percentage = coinsurance_percentage
        self.Duration_Coverage = Duration_Coverage
        self.quote_request_timestamp = quote_request_timestamp
        self.Plan_ID = Plan_ID
        self.Payment_Option = Payment_Option
        self.request_data_combination = request_data_combination
        super().__init__(stm_name, xml_text, state)

    def process_month(self, month, month_tree):
        attrs = {'Coinsurance_Percentage': self.Coinsurance_Percentage,
                 'Coinsurance_Limit': 5000,
                 'Coverage_Max': '750000',
                 'Quote_ID': self.Quote_ID,
                 'Plan_ID': self.Plan_ID,
                 'Access_Token': self.Access_Token,
                 'Duration_Coverage': self.Duration_Coverage,
                 'quote_request_timestamp': self.quote_request_timestamp,
                 'Payment_Option': self.Payment_Option,
                 'copay': '50',
                 'copay_text': 'Office Visit Copay',
                 'copay_2': '50',
                 'copay_2_text': 'Urgent Care Copay'}
        options = []
        for child in month_tree:
            match = MONTH_OPTION_PATTERN.match(child.tag)
            if match:
                mv = match.groupdict()
                mv.update({'Premium': child.text})
                options.append(mv)
            else:
                attrs[child.tag] = html.unescape(child.text)

        for opt in options:
            opt.update(attrs)
            self.monthly.append(StmPlan(self.stm_name, self.State, month, **opt))


class PremierResponse(StmQuoteResponse):
    """
    Monthly Plan
    ============
        Name - string
        Coinsurance_Percentage - int

        Benefit_Amount - int
        Out_Of_Pocket - int

        copay - int
        copay_text - str

        Premium - decimal
        AdministrativeFee - decimal
        EnrollmentFee - decimal
        GapAffordPlus_Fee - decimal
        GapAffordPlus_AdminFee - decimal
        Note - string

    Add Ons Plan
    ============
        Name - string
        Premium - decimal
        AdministrativeFee - decimal
        EnrollmentFee - decimal
        MedsenseFee - decimal
        Embeded - string [Yes/No]
    """

    copay_map = {
        '25000': '25',
        '50000': '25',
        '100000': '25',
        '250000': '25',
        '500000': '20',
        '1000000': '15'
    }

    def __init__(self, stm_name, xml_text, state, benefit_amount, out_of_pocket,
                 quote_request_timestamp, Duration_Coverage, Plan_ID):
        self.Benefit_Amount = benefit_amount
        self.Out_Of_Pocket = out_of_pocket
        self.Duration_Coverage = Duration_Coverage
        self.quote_request_timestamp = quote_request_timestamp
        self.Plan_ID = Plan_ID
        super().__init__(stm_name, xml_text, state)

    def process_month(self, month, month_tree):
        attrs = {'Benefit_Amount': self.Benefit_Amount,
                 'Out_Of_Pocket': self.Out_Of_Pocket,
                 'Duration_Coverage': self.Duration_Coverage,
                 'Quote_ID': self.Quote_ID,
                 'Plan_ID': self.Plan_ID,
                 'Access_Token': self.Access_Token,
                 'Coinsurance_Percentage': 20,
                 'quote_request_timestamp': self.quote_request_timestamp,
                 'copay': self.copay_map[str(self.Benefit_Amount)],
                 'copay_text': 'Office Visit Copay'}
        options = []
        for child in month_tree:
            match = MONTH_OPTION_PATTERN.match(child.tag)
            if match:
                mv = match.groupdict()
                for prop in child:
                    if prop.tag == 'Monthly_Cost':
                        mv['Premium'] = prop.text
                    else:
                        mv[prop.tag] = prop.text
                options.append(mv)
            else:
                attrs[child.tag] = html.unescape(child.text)
        for opt in options:
            opt.update(attrs)
            self.monthly.append(StmPlan(self.stm_name, self.State, month, **opt))


if __name__ == '__main__':
    xml_file = '/home/ahsan/Desktop/everest.xml'
    xml_res = EverestResponse('Everest STM', open(xml_file).read(), '20', '5000')
    print("is_valid: ", xml_res.is_valid())
    print(xml_res.Quote_ID)
    print(xml_res.Access_Token)
    print(xml_res.monthly)
    print(xml_res.addon_plans)
