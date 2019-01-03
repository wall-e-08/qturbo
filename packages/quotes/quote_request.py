from __future__ import unicode_literals, print_function

import re
import html
import time
import datetime
from typing import List

import requests
from xml.dom import minidom
import xml.etree.ElementTree as ET

from django.conf import settings

# from quotes.models import Carrier # TODO
# from quotes.us_states import states # TODO
from quotes.models import Carrier
from quotes.quote_response import (StmQuoteResponse, EverestResponse, HealtheFlexResponse,
                                        HealtheMedResponse, PremierResponse, SageResponse, SelectResponse,
                                        LimQuoteResponse, PrincipleResponse, UnifiedResponse, LifeShieldResponse,
                                        CardinalResponse, VitalaCareResponse, HealthChoiceResponse,
                                        LegionLimitedMedicalResponse, USADentalResponse, FoundationDentalResponse,
                                        FreedomSpiritPlusResponse, SafeguardCriticalIllnessResponse)
from quotes.us_states import states

MONTH_OPTION_PATTERN = re.compile(r'^Option(?P<option_for>\d+)$')

ADDON_ID_PATTERN = re.compile(r'^ID(?P<addon_id>\d+)$')

XML_ENCODING_PATTERN = re.compile(r'^<\?xml version="1\.0" encoding=\"iso\-8859\-1"\?>')

DATE_PATTERN = re.compile(r'^\d{2}-\d{2}-\d{4}$')

REQUEST_ATTRS = [
    'User_ID', 'State', 'Zip_Code', 'Effective_Date', 'Applicant_Gender', 'Applicant_DOB',
    'Include_Spouse', 'Spouse_Gender', 'Spouse_DOB', 'Children_Count', 'Plan_ID',
    'quote_request_timestamp', 'quote_store_key'
]

COINS_DICT = {
        '20': '80/20',
        '50': '50/50',
        '30': '70/30',
        '0': '100/0'}


class QRXmlBase(object):

    _url = settings.QUOTE_REQUEST_URL
    _headers = {"content-type": "text/xml"}
    formatted_response = None

    User_ID = settings.QUOTE_REQUEST_USER_ID

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def name(self):
        raise NotImplemented

    def attrs(self):
        raise NotImplemented

    @classmethod
    def allowed_states(cls):
        """
        :return: list of available state eg. ['AL', 'AK', 'AZ' ...]
        """
        try:
            carrier_obj = Carrier.objects.get(name=cls.Name)
        except Carrier.DoesNotExist:
            print(f"Carrier {cls.Name} not found in db.")
            return states

        return carrier_obj.get_carrier_available_states()

    @classmethod
    def is_carrier_active(cls):
        """

        :return: True if carrier model is active else False
        """
        try:
            carrier_obj = Carrier.objects.get(name=cls.Name)
        except Carrier.DoesNotExist:
            print("Carrier not found.") # TODO: Replace with logger.
            return True

        return carrier_obj.get_carrier_active_state()

    def toXML(self):
        subs = ET.Element("QuoteRequest")
        for attr in self.attrs():
            attr_value = getattr(self, attr, None)
            if attr_value is None:
                attr_value = ''
            child = ET.SubElement(subs, attr)
            getattr(self, '{0}_ele'.format(attr.lower()), self.defaultEle)(child, attr_value)

        dom = minidom.parseString(ET.tostring(subs, encoding='iso-8859-1'))
        return dom.toxml(encoding='iso-8859-1')

    def defaultEle(self, child, value):
        child.text = str(value)

    def xmlForRequest(self):
        _format = """<?xml version="1.0" encoding="iso-8859-1"?>
        <methodCall>
            <methodName>QuoteRequest</methodName>
            <params>
                <param>
                    <value><string><![CDATA[{0}]]></string></value>
                </param>
            </params>
        </methodCall>
        """
        # print("QUOTE REQUEST - {0}: {1}".format(self._get_request_data_combination(),
        #                                         self.toXML().decode('iso-8859-1')))
        return _format.format(self.toXML().decode('iso-8859-1')).encode('iso-8859-1')

    def _make_request(self):
        try:
            return requests.post(self._url, headers=self._headers, data=self.xmlForRequest(), timeout=(9, 9))
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            return None

    @classmethod
    def all(cls, data):
        raise NotImplemented

    @classmethod
    def _combination_data(cls, data):
        raise NotImplemented

    def _get_value(self, r):
        return (r.text.replace("&amp;", '&') if r.tag == 'string'
                else self._get_value(r.getchildren()[0]))

    def get_response(self):
        response = self._make_request()
        if response is not None:
            # print('########################: ', response.text)
            root = ET.fromstring(response.text)
            value = self._get_value(root)
            return XML_ENCODING_PATTERN.sub('', html.unescape(value), 1)
        return None

    def get_formatted_response(self):
        if isinstance(self.formatted_response, StmQuoteResponse):
            return self.formatted_response
        self.process_response()
        return self.formatted_response

    def get_plan_duration_coverage_value(self):
        return getattr(self, '_duration_coverage_value_for_plan', getattr(self, 'Duration_Coverage', ''))

    def _get_request_data_combination(self):
        raise NotImplemented

    def process_response(self):
        raise NotImplemented


class DependentsMixIn(object):

    fields = ['Gender', 'DOB', 'Age']

    def dependents_ele(self, dependents_attr, dependents_list):
        for dependent in dependents_list:
            self._child_ele(ET.SubElement(dependents_attr, 'Dependent'), dependent)

    def _child_ele(self, dependent_attr, dependent):
        for field in self.fields:
            field_value = dependent.get("Child_{0}".format(field), None)
            if field_value:
                child = ET.SubElement(dependent_attr, field)
                child.text = str(field_value)


class CoinsurancePercentageMixIn(object):

    def _get_coinsurance_percentage(self):
        if '/' in self.Coinsurance_Percentage:
            return self.Coinsurance_Percentage.split('/')[1]
        return self.Coinsurance_Percentage.split('_')[1]


class CoinsuranceLimitMixIn(object):

    def _get_coinsurance_limit(self):
        return self.Coinsurance_Limit.replace('$', '').replace(',', '')


class BenefitAmountMixIn(object):

    def _get_benefit_amount(self):
        return self.Benefit_Amount.replace('$', '').replace(',', '')


class CoverageDaysMixIn(object):

    def coverage_days_ele(self, child, coverage_end_date):
        if not coverage_end_date:
            child.text = ''
            self._duration_coverage_value_for_plan = ''
            return None
        if isinstance(coverage_end_date, str):
            coverage_end_date = datetime.datetime.strptime(coverage_end_date, '%m-%d-%Y').date()

        if isinstance(self.Effective_Date, str):
            coverage_days = (coverage_end_date -
                             datetime.datetime.strptime(self.Effective_Date, '%m-%d-%Y').date()).days
        else:
            coverage_days = (coverage_end_date - self.Effective_Date).days
        self._duration_coverage_value_for_plan = str(coverage_days)
        child.text = str(coverage_days)


class DurationCoverageMixIn(object):

    def duration_coverage_ele(self, child, attr_value):
        if DATE_PATTERN.match(attr_value):
            coverage_end_date = datetime.datetime.strptime(attr_value, '%m-%d-%Y').date()
            if isinstance(self.Effective_Date, str):
                coverage_days = (coverage_end_date -
                                 datetime.datetime.strptime(self.Effective_Date, '%m-%d-%Y').date()).days
            else:
                coverage_days = (coverage_end_date - self.Effective_Date).days
            self._duration_coverage_value_for_plan = str(coverage_days)
            child.text = str(coverage_days)
        else:
            self._duration_coverage_value_for_plan = str(attr_value)
            child.text = attr_value


class EverestXml(QRXmlBase, DependentsMixIn, CoinsurancePercentageMixIn,
                 BenefitAmountMixIn, DurationCoverageMixIn):

    Plan_ID = 109
    Name = "Everest STM"

    # ['80/20', '50/50', '70/30', '100/0']
    _Coin_P = {'attr': 'Coinsurance_Percentage', 'values': ['80/20', '50/50', '70/30', '100/0']}

    # ['6',]
    _D_C = {'attr': 'Duration_Coverage', 'values': ['3*2']}

    # ['2000', '3000', '4000', '5000']
    _B_A = {'attr': 'Benefit_Amount', 'values': ['2000', '3000', '4000']}

    # ['250000', '750000', '1000000', '1500000']
    _C_M = {'attr': 'Coverage_Max', 'values': ['250000', '750000', '1000000', '1500000']}

    def name(self):
        return self.Name

    def attrs(self):
        return REQUEST_ATTRS + ['Payment_Option', 'Duration_Coverage', 'Coinsurance_Percentage',
                                'Benefit_Amount', 'Coverage_Max', 'Pre_Ex_Rider',
                                'Tobacco', 'Dependents']

    @classmethod
    def all(cls, data):
        lst = []
        data_tuple_lst = []
        if int(data['Payment_Option']) == 2:
            data['Duration_Coverage'] = data.get('Coverage_Days')

        for cbn in cls._combination_data(data):
            data.update(cbn)

            # adjustment for 0% Co-Insurance Percentage
            if data['Coinsurance_Percentage'] == '100/0':
                data['Benefit_Amount'] = '0'

            data_tuple = tuple(data.values())
            if data_tuple in data_tuple_lst:
                continue
            data_tuple_lst.append(data_tuple)

            lst.append(cls(**data))
        print('EVEREST STM TOTAL REQUEST:', len(lst))
        return lst

    @classmethod
    def _combination_data(cls, data):
        if int(data['Payment_Option']) == 2:
            return [{cls._Coin_P['attr']: cp, cls._B_A['attr']: ba, cls._C_M['attr']: cm, 'Pre_Ex_Rider': 'N'}
                    for cm in cls._C_M['values'] for ba in cls._B_A['values']
                    for cp in cls._Coin_P['values']]

        return [{cls._Coin_P['attr']: cp, cls._D_C['attr']: dc,
                 cls._B_A['attr']: ba, cls._C_M['attr']: cm, 'Pre_Ex_Rider': 'N'}
                for cm in cls._C_M['values'] for ba in cls._B_A['values']
                for dc in cls._D_C['values'] for cp in cls._Coin_P['values']]

    def _get_coverage_max(self):
        return self.Coverage_Max

    def _get_request_data_combination(self):
        return "{0}-{1}-{2}-{3}-{4}-{5}".format(self.quote_store_key, self.Name, self.Duration_Coverage,
                                                self.Coinsurance_Percentage, self.Benefit_Amount,
                                                self.Coverage_Max)

    def process_response(self):
        response = self.get_response()
        if response is None:
            self.formatted_response = None
            return
        self.formatted_response = EverestResponse(self.name(), response, self.State,
                                                  self._get_coinsurance_percentage(),
                                                  self._get_benefit_amount(),
                                                  self._get_coverage_max(),
                                                  self.quote_request_timestamp,
                                                  self.get_plan_duration_coverage_value(),
                                                  self.Plan_ID, self.Payment_Option,
                                                  self._get_request_data_combination())


class HealtheFlexXml(QRXmlBase, CoinsurancePercentageMixIn, CoinsuranceLimitMixIn, CoverageDaysMixIn):

    Plan_ID = 67
    Name = 'HealtheFlex STM'
    Coverage_Max = '100000'

    _Coin_L = {'attr': 'Coinsurance_Limit', 'values': ['$20,000']}

    _Coin_P = {'attr': 'Coinsurance_Percentage', 'values': ['80_20']}

    def name(self):
        return self.Name

    def attrs(self):
        return REQUEST_ATTRS + ['Applicant_Age', 'Spouse_Age', 'Payment_Option',
                                'Coinsurance_Limit', 'Coinsurance_Percentage',
                                'Coverage_Days', 'Tobacco']

    @classmethod
    def all(cls, data):
        lst = []
        for cbn in cls._combination_data(data):
            data.update(cbn)
            lst.append(cls(**data))
        print('HealthFlex TOTAL REQUEST:', len(lst))
        return lst

    @classmethod
    def _combination_data(cls, data):
        return [{cls._Coin_L['attr']: v1, cls._Coin_P['attr']: v2} for v1 in cls._Coin_L['values']
                for v2 in cls._Coin_P['values']]

    def process_response(self):
        response = self.get_response()
        if response is None:
            self.formatted_response = None
            return
        self.formatted_response = HealtheFlexResponse(self.name(), response, self.State,
                                                      self._get_coinsurance_percentage(),
                                                      self._get_coinsurance_limit(),
                                                      self.Coverage_Max,
                                                      self.quote_request_timestamp,
                                                      self.get_plan_duration_coverage_value(),
                                                      self.Plan_ID, self.Payment_Option, self.Zip_Code)


class HealtheMedXml(QRXmlBase, CoinsurancePercentageMixIn, CoinsuranceLimitMixIn, CoverageDaysMixIn):

    Plan_ID = 56
    Name = 'HealtheMed STM'
    Coverage_Max = '2000000'

    _Coin_L = {'attr': 'Coinsurance_Limit', 'values': ['$5,000']}

    _Coin_P = {'attr': 'Coinsurance_Percentage', 'values': ['80_20', '50_50']}

    def name(self):
        return self.Name

    def attrs(self):
        return REQUEST_ATTRS + ['Payment_Option', 'Coinsurance_Limit',
                                'Coinsurance_Percentage', 'Coverage_Days', 'Tobacco']

    @classmethod
    def all(cls, data):
        lst = []
        for cbn in cls._combination_data(data):
            data.update(cbn)
            lst.append(cls(**data))
        print('HealthMed TOTAL REQUEST:', len(lst))
        return lst

    @classmethod
    def _combination_data(cls, data):
        return [{cls._Coin_L['attr']: v1, cls._Coin_P['attr']: v2} for v1 in cls._Coin_L['values']
                for v2 in cls._Coin_P['values']]

    def process_response(self):
        response = self.get_response()
        if response is None:
            self.formatted_response = None
            return
        self.formatted_response = HealtheMedResponse(self.Name, response, self.State,
                                                     self._get_coinsurance_percentage(),
                                                     self._get_coinsurance_limit(),
                                                     self.Coverage_Max,
                                                     self.quote_request_timestamp,
                                                     self.get_plan_duration_coverage_value(),
                                                     self.Plan_ID, self.Payment_Option, self.Zip_Code)


class PremierXml(QRXmlBase, DependentsMixIn, BenefitAmountMixIn):

    Plan_ID = 89
    Name = 'Premier STM'

    _D_C = {'attr': 'Duration_Coverage', 'values': ['6', '11']}

    _B_A = {'attr': 'Benefit_Amount', 'values': ['$50,000', '$100,000', '$250,000',
                                                 '$500,000', '$1,000,000']}

    def name(self):
        return self.Name

    def attrs(self):
        return REQUEST_ATTRS + ['Applicant_Age', 'Spouse_Age', 'Benefit_Amount',
                                'Out_Of_Pocket', 'Duration_Coverage', 'Tobacco', 'Dependents']

    @classmethod
    def all(cls, data):
        lst = []
        if int(data['Payment_Option']) == 2:
            return []
        for cbn in cls._combination_data(data):
            data.update(cbn)
            lst.append(cls(**data))
        print('PREMIER TOTAL REQUEST:', len(lst))
        return lst

    @classmethod
    def _combination_data(cls, data):
        cmb1 = [{cls._D_C['attr']: v1, cls._B_A['attr']: v2} for v1 in cls._D_C['values']
                for v2 in cls._B_A['values']]
        cmb = []
        for d in cmb1:
            if d['Benefit_Amount'] in ['$25,000', '$50,000', '$100,000']:
                d['Out_Of_Pocket'] = '$5,000'
                cmb.append(d)
            elif d['Benefit_Amount'] in ['$250,000', '$500,000', '$1,000,000']:
                for outOfPocket in ['$5,000', '$10,000']:
                    cmb.append(dict(Out_Of_Pocket=outOfPocket, **d))
        return cmb

    def _get_out_of_pocket(self):
        return self.Out_Of_Pocket.replace('$', '').replace(',', '')

    def process_response(self):
        response = self.get_response()
        if response is None:
            self.formatted_response = None
            return
        self.formatted_response = PremierResponse(self.Name, response, self.State,
                                                  self._get_benefit_amount(),
                                                  self._get_out_of_pocket(),
                                                  self.quote_request_timestamp,
                                                  self.get_plan_duration_coverage_value(),
                                                  self.Plan_ID)


class SageXml(QRXmlBase, DependentsMixIn, CoinsurancePercentageMixIn, DurationCoverageMixIn):

    Plan_ID = 104
    Name = 'Sage STM'

    Coverage_Max = '750000'

    Coinsurance_Limit = '5000'

    _Coin_P = {'attr': 'Coinsurance_Percentage', 'values': ['80/20', '50/50']}

    _D_C = {'attr': 'Duration_Coverage', 'values': ['3']}

    def name(self):
        return self.Name

    def attrs(self):
        return REQUEST_ATTRS + ['Payment_Option', 'Coinsurance_Percentage', 'Duration_Coverage',
                                'Applicant_Tobacco', 'Spouse_Tobacco', 'Dependents']

    @classmethod
    def all(cls, data):
        lst = []
        data['Applicant_Tobacco'] = data.get('Tobacco', 'N')
        data['Spouse_Tobacco'] = data.get('Spouse_Tobacco', 'N')
        if int(data['Payment_Option']) == 2:
            data['Duration_Coverage'] = data.get('Coverage_Days')

        for cbn in cls._combination_data(data):
            data.update(cbn)
            lst.append(cls(**data))
        print('SAGE STM TOTAL REQUEST:', len(lst))
        return lst

    @classmethod
    def _combination_data(cls, data):
        if int(data['Payment_Option']) == 2:
            return [{cls._Coin_P['attr']: v} for v in cls._Coin_P['values']]

        return [{cls._D_C['attr']: v1, cls._Coin_P['attr']: v2} for v1 in cls._D_C['values']
                for v2 in cls._Coin_P['values']]

    def _get_request_data_combination(self):
        return "{0}-{1}-{2}-{3}-{4}-{5}".format(self.quote_store_key, self.Name, self.Duration_Coverage,
                                                self.Coinsurance_Percentage, self.Coinsurance_Limit,
                                                self.Coverage_Max)

    def process_response(self):
        response = self.get_response()
        if response is None:
            self.formatted_response = None
            return
        self.formatted_response = SageResponse(self.Name, response, self.State,
                                               self._get_coinsurance_percentage(),
                                               self.quote_request_timestamp,
                                               self.get_plan_duration_coverage_value(),
                                               self.Plan_ID, self.Payment_Option,
                                               self._get_request_data_combination())


class PrincipleXml(QRXmlBase):

    Plan_ID = '54'
    Name = 'Principle Advantage'

    def attrs(self):
        return ['User_ID', 'Plan_ID', 'State', 'Zip_Code', 'Applicant_Gender', 'Applicant_Age', 'quote_store_key',
                'Include_Spouse', 'Spouse_Gender', 'Spouse_Age', 'Children_Count', 'Effective_Date', 'Tobacco']

    @classmethod
    def all(cls, data):
        lst = [cls(**data)]
        return lst

    def get_formatted_response(self):
        if isinstance(self.formatted_response, LimQuoteResponse):
            return self.formatted_response
        self.process_response()
        return self.formatted_response

    def _get_request_data_combination(self):
        return "{0}-{1}".format(self.quote_store_key, self.Name)

    def process_response(self):
        response = self.get_response()
        if response is None:
            self.formatted_response = None
            return
        self.formatted_response = PrincipleResponse(self.Name, response, self.State, self.Plan_ID,
                                                    self.quote_request_timestamp,
                                                    self._get_request_data_combination())


class UnifiedXml(QRXmlBase):

    Plan_ID = '90'
    Name = 'Unified Health One'

    def attrs(self):
        return ['User_ID', 'Plan_ID', 'State', 'Zip_Code', 'Applicant_Gender', 'Applicant_Age', 'quote_store_key',
                'Include_Spouse', 'Spouse_Gender', 'Spouse_Age', 'Children_Count', 'Effective_Date',
                'Applicant_Tobacco', 'Spouse_Tobacco']

    @classmethod
    def all(cls, data):
        lst = []
        data.update({
            'Applicant_Tobacco': data.get('Tobacco', 'N'),
            'Spouse_Tobacco': data.get('Tobacco', 'N')
        })
        lst.append(cls(**data))
        return lst

    def get_formatted_response(self):
        if isinstance(self.formatted_response, LimQuoteResponse):
            return self.formatted_response
        self.process_response()
        return self.formatted_response

    def _get_request_data_combination(self):
        return "{0}".format(self.quote_store_key)

    def process_response(self):
        response = self.get_response()
        if response is None:
            self.formatted_response = None
            return
        self.formatted_response = UnifiedResponse(self.Name, response, self.State, self.Plan_ID,
                                                  self.quote_request_timestamp)


class LifeShieldXML(QRXmlBase, DependentsMixIn, CoinsurancePercentageMixIn,
                    DurationCoverageMixIn, BenefitAmountMixIn):
    """
    The dictinaries _Coin_P, _D_C, _B_A, _C_M has a key named 'values'. It's confusing and should be addressed.
    """

    Plan_ID = 112

    Name = 'LifeShield STM'

    # '80/20', '50/50', '70/30', '100/0'
    _Coin_P = {'attr': 'Coinsurance_Percentage', 'values': ['80/20', '50/50', '70/30', '100/0']}

    _D_C = {'attr': 'Duration_Coverage', 'values': ['3*2']}

    # '2000', '3000', '4000', '5000'
    _B_A = {'attr': 'Benefit_Amount', 'values': ['2000', '3000', '4000', '5000']}

    _C_M = {'attr': 'Coverage_Max', 'values': ['250000', '750000', '1000000', '1500000']}

    def name(self):
        return self.Name

    def attrs(self):
        return REQUEST_ATTRS + ['Payment_Option', 'Duration_Coverage', 'Coinsurance_Percentage',
                                'Benefit_Amount', 'Coverage_Max', 'Tobacco', 'Dependents']

    @classmethod
    def all(cls, data):
        lst = []
        data_tuple_lst = []

        if int(data['Payment_Option']) == 2:
            data['Duration_Coverage'] = data.get('Coverage_Days')

        for cbn in cls._combination_data(data):
            data.update(cbn)

            # adjustment for 0% Co-Insurance Percentage
            if data['Coinsurance_Percentage'] == '100/0':
                data['Benefit_Amount'] = '0'

            data_tuple = tuple(data.values())
            if data_tuple in data_tuple_lst:
                continue
            data_tuple_lst.append(data_tuple)

            lst.append(cls(**data))

        print('LifeShield TOTAL REQUEST:', len(lst))
        return lst

    @classmethod
    def _combination_data(cls, data):
        if int(data['Payment_Option']) == 2:
            return [{cls._Coin_P['attr']: cp, cls._B_A['attr']: ba, cls._C_M['attr']: cm}
                    for cm in cls._C_M['values'] for ba in cls._B_A['values']
                    for cp in cls._Coin_P['values']]

        return [{cls._Coin_P['attr']: cp, cls._D_C['attr']: dc,
                 cls._B_A['attr']: ba, cls._C_M['attr']: cm}
                for cm in cls._C_M['values'] for ba in cls._B_A['values']
                for dc in cls._D_C['values'] for cp in cls._Coin_P['values']]

    @classmethod
    def set_alternative_attr(cls) -> None:
        """
        Set own Coinsurance Percentage, Benefit Amount and Coverage_Max

        :return:
        """

        current_coverage = cls._D_C['values'][0]
        dur_cov_complement_set = {'3*2', '3*1'} - {current_coverage}

        cls._D_C = {'attr': 'Duration_Coverage', 'values': list(dur_cov_complement_set)}


    def _get_coverage_max(self):
        return self.Coverage_Max

    def _get_request_data_combination(self):
        return "{0}-{1}-{2}-{3}-{4}-{5}".format(self.quote_store_key, self.Name, self.Duration_Coverage,
                                                self.Coinsurance_Percentage, self.Benefit_Amount,
                                                self.Coverage_Max)

    def process_response(self):
        response = self.get_response()
        if response is None:
            self.formatted_response = None
            return
        self.formatted_response = LifeShieldResponse(self.name(), response, self.State,
                                                     self._get_coinsurance_percentage(),
                                                     self._get_benefit_amount(),
                                                     self._get_coverage_max(),
                                                     self.quote_request_timestamp,
                                                     self.get_plan_duration_coverage_value(),
                                                     self.Plan_ID, self.Payment_Option,
                                                     self._get_request_data_combination())


class SelectXML(QRXmlBase, DependentsMixIn, CoinsurancePercentageMixIn,
                DurationCoverageMixIn, BenefitAmountMixIn):

    Plan_ID = 97

    Name = 'Select STM'

    # '80_20', '50_50', '70_30', '100_0'
    _Coin_P = {'attr': 'Coinsurance_Percentage', 'values': ['80_20', '50_50', '70_30', '100_0']}

    _D_C = {'attr': 'Duration_Coverage', 'values': ['3*1', '3*2']}

    _B_A = {'attr': 'Benefit_Amount', 'values': ['10000', '20000']}

    _C_M = {'attr': 'Policy_Max', 'values': ['100000', '250000', '1000000', '2000000']}

    def name(self):
        return self.Name

    def attrs(self):
        return REQUEST_ATTRS + ['Payment_Options', 'Payment_Option', 'Duration_Coverage', 'Policy_Max',
                                'Coinsurance_Percentage', 'Coinsurance_Max', 'Benefit_Amount', 'Dependents']

    @classmethod
    def all(cls, data):
        lst = []
        data_tuple_lst = []

        if int(data['Payment_Option']) == 2:
            data['Duration_Coverage'] = data.get('Coverage_Days')

        for cbn in cls._combination_data(data):
            data.update(cbn)

            # adjustment for 0% Co-Insurance Percentage
            if data['Coinsurance_Percentage'] == '100_0':
                data['Benefit_Amount'] = '0'

            data_tuple = tuple(data.values())
            if data_tuple in data_tuple_lst:
                continue
            data_tuple_lst.append(data_tuple)

            lst.append(cls(**data))
        print('LIFESHIELD TOTAL REQUEST:', len(lst))
        return lst

    @classmethod
    def _combination_data(cls, data):
        if int(data['Payment_Option']) == 2:
            return [{cls._Coin_P['attr']: cp, cls._B_A['attr']: ba, cls._C_M['attr']: cm}
                    for cm in cls._C_M['values'] for ba in cls._B_A['values']
                    for cp in cls._Coin_P['values']]

        return [{cls._Coin_P['attr']: cp, cls._D_C['attr']: dc,
                 cls._B_A['attr']: ba, cls._C_M['attr']: cm}
                for cm in cls._C_M['values'] for ba in cls._B_A['values']
                for dc in cls._D_C['values'] for cp in cls._Coin_P['values']]

    def _get_coverage_max(self):
        return self.Policy_Max

    def _get_request_data_combination(self):
        return "{0}-{1}-{2}-{3}-{4}-{5}".format(self.quote_store_key, self.Name, self.Duration_Coverage,
                                                self.Coinsurance_Percentage, self.Benefit_Amount,
                                                self.Policy_Max)

    def process_response(self):
        # print('Select Request:\n {}'.format(self.toXML()))
        response = None
        response = self.get_response()
        print('Select Response:\n{}'.format(response))
        if response is None:
            self.formatted_response = None
            return
        self.formatted_response = SelectResponse(self.name(), response, self.State,
                                                 self._get_coinsurance_percentage(),
                                                 self._get_benefit_amount(),
                                                 self._get_coverage_max(),
                                                 self.quote_request_timestamp,
                                                 self.get_plan_duration_coverage_value(),
                                                 self.Plan_ID, self.Payment_Option,
                                                 self._get_request_data_combination())


class CardinalChoiceXml(QRXmlBase):

    Plan_ID = '136'
    Name = 'Cardinal Choice'

    def attrs(self):
        return ['User_ID', 'Plan_ID', 'State', 'Zip_Code', 'Applicant_Gender', 'Applicant_Age',
                'Include_Spouse', 'Spouse_Gender', 'Spouse_Age', 'Children_Count', 'Tobacco']

    @classmethod
    def all(cls, data, request_options=None):
        lst = []
        lst.append(cls(**data))
        return lst

    def _get_request_data_combination(self):
        return "{0}".format(self.quote_store_key)

    def process_response(self):
        response = self.get_response()
        if response is None:
            self.formatted_response = None
            return
        self.formatted_response = CardinalResponse(self.Name, response, self.State, self.Plan_ID,
                                                   self.quote_request_timestamp, self._get_request_data_combination())


class VitalaCareXml(QRXmlBase):

    Plan_ID = '153'
    Name = 'Vitala Care'

    def attrs(self):
        return ['User_ID', 'Plan_ID', 'State', 'Zip_Code', 'Applicant_Gender', 'Applicant_Age',
                'Include_Spouse', 'Spouse_Gender', 'Spouse_Age', 'Children_Count', 'Tobacco']

    @classmethod
    def all(cls, data, request_options=None):
        lst = []
        lst.append(cls(**data))
        return lst

    def _get_request_data_combination(self):
        return "{0}".format(self.quote_store_key)

    def process_response(self):
        response = self.get_response()
        if response is None:
            self.formatted_response = None
            return
        self.formatted_response = VitalaCareResponse(self.Name, response, self.State, self.Plan_ID,
                                                   self.quote_request_timestamp, self._get_request_data_combination())


class HealthChoiceXml(QRXmlBase):

    Plan_ID = '152'
    Name = 'Health Choice'

    def attrs(self):
        return ['User_ID', 'Plan_ID', 'State', 'Zip_Code', 'Applicant_Gender', 'Applicant_Age',
                'Include_Spouse', 'Spouse_Gender', 'Spouse_Age', 'Children_Count', 'Tobacco']

    @classmethod
    def all(cls, data, request_options=None):
        lst = []
        lst.append(cls(**data))
        return lst

    def _get_request_data_combination(self):
        return "{0}".format(self.quote_store_key)

    def process_response(self):
        response = self.get_response()
        if response is None:
            self.formatted_response = None
            return
        self.formatted_response = HealthChoiceResponse(self.Name, response, self.State, self.Plan_ID,
                                                     self.quote_request_timestamp,
                                                     self._get_request_data_combination())


class LegionLimitedMedicalXml(QRXmlBase):

    Plan_ID = '122'
    Name = 'Legion Limited Medical'

    def attrs(self):
        return ['User_ID', 'Plan_ID', 'State', 'Zip_Code', 'Applicant_Gender', 'Applicant_Age',
                'Include_Spouse', 'Spouse_Gender', 'Spouse_Age', 'Children_Count', 'Tobacco']

    @classmethod
    def all(cls, data, request_options=None):
        lst = []
        lst.append(cls(**data))
        return lst

    def _get_request_data_combination(self):
        return "{0}".format(self.quote_store_key)

    def process_response(self):
        response = self.get_response()
        if response is None:
            self.formatted_response = None
            return
        self.formatted_response = LegionLimitedMedicalResponse(self.Name, response, self.State, self.Plan_ID,
                                                       self.quote_request_timestamp,
                                                       self._get_request_data_combination())


class USADentalXml(QRXmlBase):
    Plan_ID = '151'
    Name = 'USA Dental'

    def attrs(self):
        return ['User_ID', 'Plan_ID', 'State', 'Zip_Code', 'Applicant_Gender', 'Applicant_Age',
                'Include_Spouse', 'Spouse_Gender', 'Spouse_Age', 'Children_Count', 'Tobacco']

    @classmethod
    def all(cls, data, request_options=None):
        lst = []
        lst.append(cls(**data))
        return lst

    def _get_request_data_combination(self):
        return "{0}".format(self.quote_store_key)

    def process_response(self):
        response = self.get_response()
        if response is None:
            self.formatted_response = None
            return
        self.formatted_response = USADentalResponse(self.Name, response, self.State, self.Plan_ID,
                                                               self.quote_request_timestamp,
                                                               self._get_request_data_combination())


class FoundationDentalXml(QRXmlBase):
    Plan_ID = '48'
    Name = 'Foundation Dental'
    product_type = 'main'
    Include_FoundationVision = '0'
    applicant_data = None

    def attrs(self):
        return ['User_ID', 'Plan_ID', 'State', 'Zip_Code', 'Applicant_Gender', 'Applicant_Age',
                'Include_Spouse', 'Spouse_Gender', 'Spouse_Age', 'Children_Count', 'Tobacco', 'Include_FoundationVision']

    @classmethod
    def all(cls, data, request_options=None):
        lst = []
        lst.append(cls(**data))
        return lst

    def _get_request_data_combination(self):
        return "{0}".format(self.quote_store_key)

    def process_response(self):
        response = self.get_response()
        if response is None:
            self.formatted_response = None
            return
        self.formatted_response = FoundationDentalResponse(self.Name, response, self.Plan_ID,
                                                           self.quote_request_timestamp,
                                                           self.applicant_data,
                                                           self.product_type)

class FreedomSpiritPlusXml(QRXmlBase):

    Plan_ID = '64'
    Name = 'Freedom Spirit Plus'
    applicant_data = None
    product_type = 'main'

    def attrs(self):
        return ['User_ID', 'Plan_ID', 'State', 'Zip_Code', 'Applicant_Gender', 'Applicant_Age', 'Tobacco']

    @classmethod
    def all(cls, data, request_options=None, request=None):
        if request:
            data['request'] = request

        lst = [cls(**data)]
        print("connection: {0}".format(len(lst)))
        return lst

    def process_response(self):
        response = self.get_response()
        if response is None:
            self.formatted_response = None
            return
        self.formatted_response = FreedomSpiritPlusResponse(self.Name, response, self.State, self.Plan_ID,
                                                            self.quote_request_timestamp,
                                                            self.applicant_data, self.Plan_ID,
                                                            self.product_type)

class SafeguardCriticalIllnessXml(QRXmlBase):

    Plan_ID = '88'
    Name = 'Safeguard Critical Illness'
    product_type = 'main'
    applicant_data = None

    def attrs(self):
        return ['User_ID', 'Plan_ID', 'State', 'Zip_Code', 'Applicant_Gender', 'Applicant_Age',
                'Include_Spouse', 'Spouse_Gender', 'Spouse_Age', 'Children_Count', 'Tobacco']

    def _get_request_data_combination(self):
        return "{0}".format(self.quote_store_key)

    @classmethod
    def all(cls, data, request_options=None, request=None):
        if request:
            data['request'] = request

        lst = [cls(**data)]
        return lst

    def process_response(self):
        response = self.get_response()
        if response is None:
            self.formatted_response = None
            return
        self.formatted_response = SafeguardCriticalIllnessResponse(
            self.Name, response, self.State, self.Plan_ID,
            self.quote_request_timestamp,
            self._get_request_data_combination())


insurance_selector = {
    'stm': [EverestXml, LifeShieldXML],
    'lim': [CardinalChoiceXml, VitalaCareXml, HealthChoiceXml, LegionLimitedMedicalXml],
    'anc': [USADentalXml, FoundationDentalXml, FreedomSpiritPlusXml, SafeguardCriticalIllnessXml]
}


def get_xml_requests(data: dict, alt_cov_flag: bool = False) -> List[QRXmlBase]:
    """
    This is the class that is called by celery to create initial quote
    request xml for sending.

    :param data: Quote request form data
    :type data: Python dictionary
    :param alt_cov_flag: alternative coverage flag; If this is set we'll get a different request for stm.
    :type alt_cov_flag: bool
    :return: list of xml objects
    """
    print("packages/quotes/quote_request.py -- Line No. 770")
    print('\n\nget_xml_class data: ', data)
    print('\n\nins_type: ', data['Ins_Type'])

    app_state = data['State']
    xml_requests = []


    for xml_cls in insurance_selector[data['Ins_Type']]:
        if app_state in xml_cls.allowed_states() and xml_cls.is_carrier_active():
            print(f"{xml_cls.Name} is available in state: {app_state}")
            if alt_cov_flag is True and data['Ins_Type'] == 'stm':
                print(f'Setting alternative coverage options for {xml_cls.Name}')
                xml_cls.set_alternative_attr()
            xml_requests += xml_cls.all(data)
        else:
            print(f"{xml_cls.Name} is NOT available in state: {app_state}")


    print("xml_request objects: ", xml_requests.__str__())
    print("Returning xml requests.")
    return xml_requests
