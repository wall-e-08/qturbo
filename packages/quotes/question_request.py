from __future__ import print_function, unicode_literals

import re
import html
import requests
from xml.dom import minidom
import xml.etree.ElementTree as ET

from django.conf import settings

from .logger import VimmLogger


logger = VimmLogger('quote_turbo')

XML_ENCODING_PATTERN = re.compile(r'^<\?xml version="1\.0" encoding=\"iso\-8859\-1"\?>')


class QuestionXmlBase(object):

    _url = settings.QUOTE_REQUEST_URL
    _headers = {"content-type": "text/xml"}
    formatted_response = None

    User_ID = settings.QUOTE_REQUEST_USER_ID

    def __init__(self, quote_id, selected_addon_plans=None, **kwargs):
        self.Quote_ID = quote_id
        self.Add_ons = selected_addon_plans or None
        for key, value in kwargs.items():
            setattr(self, key, value)

    def name(self):
        raise NotImplemented

    def attrs(self):
        if self.Add_ons:
            return ['User_ID', 'Quote_ID', 'Add-ons']
        return ['User_ID', 'Quote_ID']

    def toXML(self):
        subs = ET.Element("HealthQuestion")
        for attr in self.attrs():
            attr_value = getattr(self, attr.replace('-', '_'), None)
            if attr_value is None:
                attr_value = ''
            child = ET.SubElement(subs, attr)
            getattr(self, '{0}_ele'.format(attr.replace('-', '_').lower()), self.defaultEle)(child, attr_value)

        dom = minidom.parseString(ET.tostring(subs, encoding='iso-8859-1'))
        return dom.toxml(encoding='iso-8859-1')

    def defaultEle(self, child, value):
        child.text = str(value)

    def add_ons_ele(self, child, add_ons):
        for add_on in add_ons:
            grand_child = ET.SubElement(child, 'ID')
            grand_child.text = str(add_on['addon_id'])

    def xmlForRequest(self):
        _format = """<?xml version="1.0" encoding="iso-8859-1"?>
        <methodCall>
            <methodName>STMHealthQuestion</methodName>
            <params>
                <param>
                    <value><string><![CDATA[{0}]]></string></value>
                </param>
            </params>
        </methodCall>
        """
        return _format.format(self.toXML().decode('iso-8859-1')).encode('iso-8859-1')

    def _make_request(self):
        return requests.post(self._url, headers=self._headers, data=self.xmlForRequest())

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
        root = ET.fromstring(response.text)
        value = self._get_value(root)
        return XML_ENCODING_PATTERN.sub('', html.unescape(value), 1)

    def get_formatted_response(self):
        logger.info(self.get_response())
        if isinstance(self.formatted_response, QuestionResponse):
            return self.formatted_response
        self.process_response()
        return self.formatted_response

    def process_response(self):
        self.formatted_response = QuestionResponse(self.Quote_ID, self.get_response())


class QuestionResponse(object):

    def __init__(self, quote_id, xml_text):
        self.quote_id = quote_id
        self.xml_text = xml_text
        logger.info("QuestionResponse: {0}".format(self.xml_text))
        self.root = ET.fromstring(self.xml_text)
        self.g_order = 0
        self.stm_questions = {}

        self.process()

    def process(self):
        processors = {
            'Que': self.process_que,
            'Add-ons': self.process_addon,
        }
        order = 0
        for child in self.root:
            try:
                processors[child.tag](child, order)
            except KeyError:
                if str(child.tag) == 'Note':
                    continue
            order += 1

    def process_que(self, que_tree, order):
        question = {'order': order}
        sub_order = 0
        for child in que_tree:
            if child.tag == 'ExpectedAnswers':
                question[child.tag] = child.text.split('/')
            elif child.tag == 'SubQue':
                self.process_sub_que(child, sub_order, question)
                sub_order += 1
            else:
                question[child.tag] = child.text
        question['user_answer'] = None
        if 'CorrectAnswer' not in question and question.get('ExpectedAnswers'):
            question['CorrectAnswer'] = 'No' if 'US citizen' in question['ExpectedAnswers'] else 'Yes'
        self.stm_questions[question['ID']] = question
        if question.get('SubQue', None) is None:
            question['g_order'] = self.g_order
            self.g_order += 1

    def process_sub_que(self, sub_que_tree, sub_order, question):
        sub_question = {'sub_order': sub_order}
        for child in sub_que_tree:
            if child.tag == 'ExpectedAnswers':
                sub_question[child.tag] = child.text.split('/')
            elif child.tag == 'Text':
                sub_question[child.tag] = "{0} {1}".format(question['Text'], child.text)
            else:
                sub_question[child.tag] = child.text
        sub_question['user_answer'] = None
        sub_question['order'] = question['order']
        sub_question['parent_id'] = question['ID']
        sub_question['g_order'] = self.g_order
        if 'CorrectAnswer' not in sub_question:
            sub_question['CorrectAnswer'] = 'No' if 'US citizen' in sub_question['ExpectedAnswers'] else 'Yes'
        self.g_order += 1
        try:
            question['SubQue'].append(sub_question)
        except KeyError:
            question['SubQue'] = [sub_question]

    def process_addon(self, addon_tree, order):
        pass


def get_stm_questions(quote_id, selected_addon_plans=None):
    xml = QuestionXmlBase(quote_id=quote_id, selected_addon_plans=selected_addon_plans)
    return xml.get_formatted_response().stm_questions
