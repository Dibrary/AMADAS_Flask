
from opc_module import *
from VO.lims import LIMS
from VO.device import device
from VO.report import report

class OpcController: # main파일과 opc_module 파일 사이에 연결 역할.
    def __init__(self, object_tag, taggs, user_id=None):
        self.object_tag = object_tag
        self.taggs = taggs
        self.user_id = user_id
        self.opcmodule = withOPC(object_tag, taggs)

    def analyzer_state_for_house(self):
        ana_state_value = []
        try:
            for i in range(0, len(self.taggs)):
                ana_tag = self.taggs[i][1]
                ana_state_value.append(self.read_Analyzer_state(ana_tag, self.taggs[i]))
            print(ana_state_value)
            result = ''
            for i in range(0, len(ana_state_value)):
                if i == (len(ana_state_value) - 1):
                    result += str(ana_state_value[i])
                else:
                    result += str(ana_state_value[i]) + ","
            print(result)
            return result
        except Exception as e:
            result = ''
            for i in range(0, len(self.taggs)):
                if i == (len(self.taggs) -1): result += "6"
                else:                         result += "6,"
            return result # 6은 브라우저에서 breakdown이 빨간색으로 나타난다.

    def analyzer_state_for_analyzer(self):
        try:
            ana_state_value = self.read_Analyzer_state(self.object_tag, self.taggs)
            return str(ana_state_value)
        except Exception as e:
            return "6" # 6은 브라우저에서 breakdown이 빨간색으로 나타난다.

    def read_Analyzer_state(self, ana_tag, taggs):
        try:
            anaOPC = withOPC(ana_tag, taggs)
            result = anaOPC.read_Analyzer_state()
            return result
        except Exception as e:
            return "6"

    def check_dcs_permit(self):
        result = self.opcmodule.check_dcs_permit()
        return result

    def check_dcs_start_validation(self):
        result = self.opcmodule.check_dcs_start_validation()
        return result

    def request_validation(self, bottle_tag):
        result = self.opcmodule.request_Validation(bottle_tag)
        return result

    def request_validation_scheduler(self):
        self.opcmodule.request_Validation_scheduler()

    def request_maintenance(self):
        result = self.opcmodule.request_Maintenance()
        return result

    def start_maintenance(self):
        result = self.opcmodule.start_Maintenance(self.user_id)
        return result

    def stop_maintenance(self):
        result = self.opcmodule.stop_Maintenance(self.user_id)
        return result

    def calibration(self):
        result = self.opcmodule.calibration(self.user_id)
        return result

    def lims_comparison(self, lims_data):
        result = self.opcmodule.lims_Comparison(lims_data)
        return result

    def start_Validation(self, valve_signal, order_type, user_id, bottle_tag):
        result = self.opcmodule.start_Validation_preprocess(valve_signal, order_type, self.object_tag, user_id,
                                                            bottle_tag)
        return result

    def change_semi_auto_tag(self):
        result = self.opcmodule.change_semi_auto_tag(self.user_id)
        return result

    def LIMS_recognize_from_button(self, index: int):
        self.opcmodule.LIMS_recognize_from_button(index)

    def LIMS_recognize_from_limsDB(self, index: int):
        self.opcmodule.LIMS_recognize_from_limsDB(index)

    def realtime_Analyzerstate(self):
        self.opcmodule.realtime_Analyzerstate()

    def stop_manual_validation(self):
        result = self.opcmodule.change_semi_auto_tag(self.user_id)  # manual방식 끝났다는 신호를 semi_auto 태그 트리거로 준다.
        return result
