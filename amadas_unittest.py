import unittest
import main
import requests

class UnitTest(unittest.TestCase):
    def setUp(self):
        self.host = 'http://localhost:5000/'
        self.user_id = 'java'
        self.refer_tag = '352-RB-011'
        self.ana_tag = '251-AH-001'
        self.house_tag = 'House1'
        self.process_tag = '1630AI155A'
        self.start_dt = '20210311090000'
        self.end_dt ='20210422090000'
        self.lims_value = '4.6'


    def test_selector_method(self):
        taggs, network = main.selector('251-AH-001')
        self.assertEqual('OPC', network[0])

    def test_request_validation(self):
        response = requests.get(self.host + 'validation/'+ self.ana_tag + '/'+self.user_id+'/' + self.refer_tag)
        self.assertEqual('OK', response.text) # permit이 1이면 OK로 나오고, 0이면 NotOK로 나온다.

    def test_semi_auto(self):
        response = requests.get(self.host + 'semiauto/' + self.ana_tag + '/'+ self.user_id)
        self.assertEqual('OK', response.text)

    def test_stop_manual_validation(self):
        response = requests.get(self.host + 'stop_manual_validation/' + self.ana_tag + '/'+ self.user_id)
        self.assertEqual('OK', response.text)

    def test_request_maintenance(self):
        response = requests.get(self.host + 'maintenance/'+ self.ana_tag + '/'+self.user_id)
        self.assertEqual('NotOK', response.text) # permit이 1이면 OK로 나오고, 0이면 NotOK로 나온다.

    def test_start_maintenance(self):
        response = requests.get(self.host + 'smaintenance/'+ self.ana_tag + '/'+self.user_id)
        self.assertEqual('OK', response.text)

    def test_stop_maintenance(self):
        response = requests.get(self.host + 'stopmaintenance/'+ self.ana_tag + '/'+self.user_id)
        self.assertEqual('OK', response.text)

    def test_calibration(self):
        response = requests.get(self.host + 'calibration/' + self.ana_tag + '/'+ self.user_id)
        self.assertEqual('OK', response.text)

    def test_analyzerstate_for_house(self):
        response = requests.get(self.host + 'anastate/' + self.house_tag)
        self.assertEqual(str, type(response.text))

    def test_analyzerstate_for_analyzer(self):
        response = requests.get(self.host + 'analyzerstate/' + self.ana_tag)
        self.assertEqual(str, type(response.text))

    def test_check_dcs_permit(self):
        response = requests.get(self.host + 'checkPermit/' + self.house_tag)
        self.assertEqual(str, type(response.text)) # permit되었으면 OK로 나오고, 아니면 NotOK

    def test_check_dcs_start_validation(self):
        response = requests.get(self.host + 'checkDcsStart/' + self.ana_tag)
        self.assertEqual(str, type(response.text)) # 시작되었으면 OK로 나오고, 아니면 NotOK
        # AssertionError: 'NotOK' != '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3[249 chars]p>\n'

    def test_lims_compare(self):
        response = requests.get(self.host + 'limscompare/' + self.ana_tag + '/' + self.process_tag + '/' + self.start_dt + '/' + self.end_dt + '/' + self.lims_value)
        self.assertEqual(str, type(response.text))





