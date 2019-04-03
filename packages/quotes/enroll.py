from __future__ import print_function, unicode_literals

import re
import html
import uuid
import string
import requests
from xml.dom import minidom
from django.conf import settings
import xml.etree.ElementTree as ET

from .logger import VimmLogger


logger = VimmLogger('quote_turbo')

XML_ENCODING_PATTERN = re.compile(r'^<\?xml version="1\.0" encoding=\"iso\-8859\-1"\?>')

PREVIOUSLY_ENROLLED_ERROR_TEXT = "Your other STM insurance coverage termination date"


class Enroll(object):

    _url = settings.QUOTE_ENROLL_URL
    _headers = {"content-type": "text/xml"}
    formatted_response = None

    User_ID = settings.QUOTE_REQUEST_USER_ID

    ATTRS = ['Plan_ID', 'User_ID']

    def __init__(self, attr_data, applicant_data, payment_data, question_data,
                 parent_data=None, dependents_data=None, add_on_plans_data=None):
        for k, v in attr_data.items():
            setattr(self, k, v)
        self.applicant_data = applicant_data
        self.payment_data = payment_data
        self.question_data = question_data
        self.parent_data = parent_data if parent_data else {}
        self.dependents_data = dependents_data
        self.add_on_plans_data = add_on_plans_data or None

    def toXML(self):
        subs = ET.Element("NewBusiness")
        for attr in self.ATTRS:
            child = ET.SubElement(subs, attr)
            child.text = str(getattr(self, attr))
        # applicant info
        for attr, attr_value in self.applicant_data.items():
            if attr[0] not in string.ascii_uppercase:
                continue
            child = ET.SubElement(subs, attr)
            child.text = str(attr_value)
        # payment info
        for attr, attr_value in self.payment_data.items():
            if attr[0] not in string.ascii_uppercase:
                continue
            child = ET.SubElement(subs, attr)
            child.text = str(attr_value)
        # question info
        question_element = ET.SubElement(subs, 'STMHealthQuestion')
        for question in self.question_data:
            que = ET.SubElement(question_element, 'Que')
            ID = ET.SubElement(que, 'ID')
            ID.text = str(question['ID'])
            if question.get('SubQue', None) is None:
                Answer = ET.SubElement(que, 'Answer')
                Answer.text = str(question['user_answer'])
            else:
                for sub_question in question['SubQue']:
                    sub_que = ET.SubElement(que, 'SubQue')
                    sub_ID = ET.SubElement(sub_que, 'ID')
                    sub_ID.text = str(sub_question['ID'])
                    sub_Answer = ET.SubElement(sub_que, 'Answer')
                    sub_Answer.text = str(sub_question['user_answer'])
        # parent info
        for attr, attr_value in self.parent_data.items():
            if attr[0] not in string.ascii_uppercase:
                continue
            child = ET.SubElement(subs, attr)
            child.text = str(attr_value)
        # dependents info
        if self.dependents_data:
            dependents_element = ET.SubElement(subs, 'Dependents')
            for dependent in self.dependents_data:
                dependent_element = ET.SubElement(dependents_element, 'Dependent')
                for attr, attr_value in dependent.items():
                    if attr[0] not in string.ascii_uppercase:
                        continue
                    child = ET.SubElement(dependent_element, attr)
                    child.text = str(attr_value)

        # add-on plans info
        if self.add_on_plans_data:
            add_on_element = ET.SubElement(subs, 'Add-ons')
            for add_on_plan in self.add_on_plans_data:
                add_on_id_element = ET.SubElement(add_on_element, 'ID{0}'.format(add_on_plan['addon_id']))
                add_on_plan_element = ET.SubElement(add_on_id_element, 'Plan')
                for add_on_attr in ['Name', 'Premium', 'AdministrativeFee', 'EnrollmentFee']:
                    add_on_attr_element = ET.SubElement(add_on_plan_element, add_on_attr)
                    add_on_attr_element.text = str(add_on_plan[add_on_attr])
                if str(add_on_plan['addon_id']) == '38':
                    for add_on_attr in ['Plan', 'Plan_Code', 'Deductible']:
                        add_on_attr_element = ET.SubElement(add_on_plan_element, add_on_attr)
                        add_on_attr_element.text = str(add_on_plan[add_on_attr])
        dom = minidom.parseString(ET.tostring(subs, encoding='iso-8859-1'))
        return dom.toxml(encoding='iso-8859-1')

    def _make_request(self):
        pretty_xml = minidom.parseString(self.toXML().decode("iso-8859-1")).toprettyxml()
        print(f'\n------------------------------\n'
              f'HII_New_Business request XML :\n'
              f'------------------------------\n'
              f'{pretty_xml}')
        return requests.post(self._url, data={'HII_New_Business': self.toXML().decode('iso-8859-1')})

    def _get_value(self, r):
        return (r.text.replace("&amp;", '&') if r.tag == 'string'
                else self._get_value(r.getchildren()[0]))

    def get_response(self):
        response = self._make_request()
        return XML_ENCODING_PATTERN.sub('', html.unescape(response.text), 1)


class Response(object):

    def __init__(self, xml_text):
        logger.info("Enroll Response: {0}".format(xml_text))
        self.escaped_xml_text = xml_text.replace('&', '&amp;').replace('"', '&quot;').replace("'", '&#39;')
        self.root = ET.fromstring(self.escaped_xml_text)

        self.applicant = {}
        self.error = None

        self.process()

    def process(self):
        processors = {
            'Message': self.process_message,
            'Success': self.process_success,
            'Applicant': self.process_applicant,
            'Error': self.process_error
        }
        for child in self.root:
            try:
                processors[child.tag.replace("_", '')](child)
            except KeyError:
                if child.tag not in []:
                    raise

    def process_applicant(self, applicant_tree):
        processors = {
            "Dependent": self.sub_processor_dependent,
            "Add-ons": self.sub_processor_add_ons
        }
        for child in applicant_tree:
            try:
                processors[child.tag](child)
            except KeyError:
                self.applicant[child.tag] = child.text

    def process_success(self, success_tree):
        processors = {
            "Applicant": self.process_applicant,
        }
        for child in success_tree:
            try:
                processors[child.tag](child)
            except KeyError:
                if child.tag not in []:
                    raise

    def sub_processor_dependent(self, dependent_tree):
        dependent = {}
        for child in dependent_tree:
            dependent[child.tag] = child.text
        try:
            self.applicant['Dependent'].append(dependent)
        except KeyError:
            self.applicant['Dependent'] = [dependent]

    def sub_processor_add_ons(self, add_ons_tree):
        addons = []
        for child in add_ons_tree:
            addon = {'ID': child.tag[2:]}
            for grand_child in child:
                addon[grand_child.tag] = grand_child.text
            addons.append(addon)
        self.applicant['Add_ons'] = addons

    def process_message(self, message_tree):
        # print(dir(message_tree))
        if message_tree.text:
            self.applicant['Message'] = message_tree.text
        for child in message_tree:
            self.applicant[child.tag] = child.text

    def process_error(self, error_tree):
        self.error = error_tree.find('Message').text


class ESignResponse(Response):

    def process(self):
        processors = {
            'Success': self.process_success,
            'Applicant': self.process_applicant,
            'Error': self.process_error,
            'Add-ons': self.sub_processor_add_ons,
        }
        for child in self.root:
            try:
                processors[child.tag.replace("_", '')](child)
            except KeyError:
                if child.tag not in ['Message', 'Quote_ID', 'Access_Token', 'ApplicantID']:
                    logger.info('Unhandled xml tag: {}'.format(child.tag))
                    pass
                else:
                    self.applicant[child.tag] = child.text


class ESignVerificationEnroll(object):

    _url = settings.ESIGNATURE_VERIFICATION_URL

    _headers = {"content-type": "text/xml"}

    formatted_response = None

    ATTRS = ['Quote_ID', 'ApplicantID', 'Access_Token', 'Process_Option']

    def __init__(self, attr_data, request=None):
        self.request = request
        for k, v in attr_data.items():
            setattr(self, k, v)
        self.User_ID = 'A15A09AB0074499D17B31C'

    def toXML(self):
        subs = ET.Element("EsignPaymentProcess")
        for attr in self.ATTRS:
            child = ET.SubElement(subs, attr)
            child.text = str(getattr(self, attr))

        # Resend esign send method
        if getattr(self, 'Process_Option') == 'resend':
            child = ET.SubElement(subs, 'ESign_Send_Method')
            child.text = str(getattr(self, 'ESign_Send_Method'))

        dom = minidom.parseString(ET.tostring(subs, encoding='iso-8859-1'))
        return dom.toxml(encoding='iso-8859-1')

    def _make_request(self):
        logger.info("ESign Verification Enroll request, EnrollRequest_XML: {0}, user_info: {1}, request_id:{2}".format(self.toXML().decode('iso-8859-1'), self.request, str(uuid.uuid4())))
        return requests.post(self._url, data={'payment': self.toXML().decode('iso-8859-1')}, timeout=(60, 15))

    def _get_value(self, r):
        return (r.text.replace("&amp;", '&') if r.tag == 'string'
                else self._get_value(r.getchildren()[0]))

    def get_response(self):
        response = self._make_request()
        logger.info("ESign Verification Enroll response (formatted) from HII server, EnrollResponse_XML:{0}, user_info:{1}".format(response.text, self.request))

        # print("response.text: ", response.text)
        return XML_ENCODING_PATTERN.sub('', html.unescape(response.text), 1)
