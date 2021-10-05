
from db_module import *
from modbus_module import *

from VO.device import device
from VO.lims import LIMS
from VO.report import report


class ModbusController: # main파일과 modbus_module파일 사이에 연결 역할.
    def __init__(self, object_tag, taggs, user_id=None):
        self.object_tag = object_tag
        self.taggs = taggs
        self.user_id = user_id
        self.modbusmodule = withMODBUS(object_tag, taggs)

    def analyzer_state_for_house(self):
        try:
            ana_state_value = []
            for i in range(0, len(self.taggs)):
                ana_tag = self.taggs[i][1]
                ana_state_value.append(self.read_Analyzer_state(ana_tag, self.taggs[i]))
            result = ''
            for i in range(0, len(ana_state_value)):
                if i == (len(ana_state_value) - 1):
                    result += str(ana_state_value[i])
                else:
                    result += str(ana_state_value[i]) + ","
            return result
        except Exception as e:
            result = ''
            for i in range(0, len(self.taggs)):
                if i == (len(self.taggs) -1): result += "6"
                else:                         result += "6,"
            return result

    def analyzer_state_for_analyzer(self):
        try:
            ana_state_value = self.read_Analyzer_state(self.object_tag, self.taggs)
            return str(ana_state_value)
        except Exception as e:
            return "6"

    def read_Analyzer_state(self, ana_tag, taggs):
        try:
            anaMODBUS = withMODBUS(ana_tag, taggs)
            result = anaMODBUS.read_Analyzer_state()
            return result
        except Exception as e:
            return "6"

    def check_dcs_permit(self):
        result = self.modbusmodule.check_dcs_permit()
        return result

    def check_dcs_start_validation(self):
        result = self.modbusmodule.check_dcs_start_validation()
        return result

    def request_validation(self, bottle_tag):
        try:
            result = self.modbusmodule.request_Validation(bottle_tag)
            return result
        except Exception as e:
            return "6"

    def request_validation_scheduler(self):
        self.modbusmodule.request_Validation_scheduler()

    def request_maintenance(self):
        try:
            result = self.modbusmodule.request_Maintenance()
            return result
        except Exception as e:
            return "6"

    def start_maintenance(self):
        try:
            result = self.modbusmodule.start_Maintenance(self.user_id)
            return result
        except Exception as e:
            return "6"

    def stop_maintenance(self):
        try:
            result = self.modbusmodule.stop_Maintenance(self.user_id)
            return result
        except Exception as e:
            return "6"

    def calibration(self):
        try:
            result = self.modbusmodule.calibration(self.user_id)
            return result
        except Exception as e:
            return "6"

    def lims_comparison(self, process_tag, start_dt, end_dt, process_value):
        result = self.modbusmodule.lims_Comparison(process_tag, start_dt, end_dt, process_value)
        return result

    def start_Validation(self, valve_signal, order_type, user_id, bottle_tag):
        result = self.modbusmodule.start_Validation_preprocess(valve_signal, order_type, self.object_tag, user_id,
                                                               bottle_tag)
        return result

    def change_semi_auto_tag(self):
        try:
            result = self.modbusmodule.change_semi_auto_tag(self.user_id)
            return result
        except Exception as e:
            return "6"

    def LIMS_recognize_from_button(self, index: int):
        self.modbusmodule.LIMS_recognize_from_button(index)

    def LIMS_recognize_from_limsDB(self, index: int):
        self.modbusmodule.LIMS_recognize_from_limsDB(index)

    def realtime_Analyzerstate(self):
        self.modbusmodule.realtime_Analyzerstate()

    def save_manual_validation(self):
        try:
            result = self.opcmodule.save_manual_validation()
            return result
        except Exception as e:
            return "Error Save Manual Validationing"

    def stop_manual_validation(self):
        try:
            result = self.modbusmodule.change_semi_auto_tag(self.user_id)
            return result
        except Exception as e:
            return "Error Stop Manual Validationing"