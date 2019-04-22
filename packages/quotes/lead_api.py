import requests
from django.conf import settings
import xml.etree.ElementTree as ET


class LeadCampaignApi(object):
    lead_api_url = settings.LEAD_GATEWAY_ADDRESS
    camp_id = settings.LEAD_CAMPAIGN_ID
    is_test = settings.LEAD_IS_TEST

    def __init__(self, **kwargs):
        self.error = None
        self.data = None
        self.json_data = {}
        try:
            self.content = {
                "CampaignId": "{}".format(self.camp_id),
                "IsTest": "{}".format(self.is_test),
                "FirstName": "{}".format(kwargs['First_Name']),
                "LastName": "{}".format(kwargs['Last_Name']),
                "Address1": "{}".format(kwargs['Address']),
                "City": "{}".format(kwargs['City']),
                "State": "{}".format(kwargs['State']),
                "Zip": "{}".format(kwargs['ZipCode']),
                "DOB": "{}".format(kwargs['DOB']),
                "Email": "{}".format(kwargs['Email']),
                "Phone": "{}".format(kwargs['DayPhone'].replace('-', '')),
                "AltPhone": "{}".format(kwargs['CellPhone'].replace('-', '')),
                "Gender": "{}".format(kwargs['Gender'][0]),
                "Smoker": "{}".format('Yes' if kwargs['Tobacco'] == 'Y' else 'No'),
                # "IPAddress": "",
                # "ThankYouRedirect": "",
                # "FailureRedirect": "",
                # "AppendResponseCodeToRedirect": "",
            }
            print(self.content)
        except (KeyError, TypeError) as err:
            print("Wrong form data provided.. \nError: {}\n".format(err))
            self.content = {}

    def get_response(self):
        # print("api url: ", self.lead_api_url)
        # print("content for api: ", self.content)
        try:
            response = requests.post(self.lead_api_url, data=self.content)
            if response.status_code == 200:
                self.data = response.text.replace('ï»¿', '')
                # print("Got data: {}".format(self.data))
                return self.data
            else:
                print("Request response code: {}".format(response.status_code))
        except requests.exceptions.RequestException as err:
            print("request error - {}: {}".format(self.__class__.__name__, err))
        return None

    def get_lead_id(self):
        self.get_response()
        root = ET.ElementTree(ET.fromstring(self.data)).getroot()
        json_data = {}
        for child in root:
            print("Tag: {}, Attr: {}, Txt: {}".format(child.tag, child.attrib, child.text))
            json_data[child.tag] = child.text
        print("\n\nJSON DATA: \n{}\n".format(json_data))
        self.json_data = json_data
        if json_data.get('IsValid') and json_data.get('IsValid') == 'True':
            print("Lead id: {}".format(json_data.get('LeadId')))
            return json_data.get('LeadId')
        return None


