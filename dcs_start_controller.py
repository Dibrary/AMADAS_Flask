from lxml import etree
from threading import *

from db_module import *
from opc_module import *
from modbus_module import *

class DCS_start_validation: # dcs_start_validation 상태 확인
    def __init__(self):
        root = (etree.parse("opc_modbus_db_ip.xml")).getroot()
        for j in root.iter("address"):  self.version = int(j.findtext("version"))
        if self.version == 2 or self.version == 3 or self.version == 4:
            self.network = "MODBUS"
            for i in root.iter("slave"):
                self.dcsip = (i.findtext("dcsip"))[:13]  # dcs ip
                self.dcsport = (i.findtext("dcsip"))[14:]  # dcs port
                self.gcip = (i.findtext("gcip"))[:13]  # gc ip
                self.gcport = (i.findtext("gcip"))[14:]  # gc port
        else:
            self.network = "OPC"
            for k in root.iter("server"):   self.url = k.findtext("url")

        self.round_check_dcs_start_validation()

    def check_alarm_fault(self, module, index, alarm_tag, fault_tag):
        alarm_value, fault_value = module.check_alarm_fault(index, alarm_tag, fault_tag)
        return alarm_value, fault_value

    def round_check_dcs_start_validation(self): # browser 사용자 모르게, dcs에서 start_validation으로 자체 시작 신호를 보낼 경우 동작한다.
        self.analyzer_taggs = []
        self.taggs = []
        default_valve = []
        default_valid_type = []
        default_bottle = []
        db = withDB()
        analyzer_taggs = db.selectAllAnalyzer() # 반환 꼴은 ((analyzer_정보, analyzer_정보, analyzer_정보)) 꼴
        for i in range(0, len(analyzer_taggs)):
            self.analyzer_taggs.append(analyzer_taggs[i][0])
            default_valve.append(db.selectDefaultValveByTag(analyzer_taggs[i][0]))
            default_bottle.append(db.selectDefaultBottleTagByTag(analyzer_taggs[i][0]))
            default_valid_type.append(db.selectDefaultValidationTypeByTag(analyzer_taggs[i][0]))
        flag = ''
        if self.version == 1 or self.version == 2:
            flag = "OPC"
        elif self.version == 3 or self.version == 4:
            flag = "MODBUS"

        for k in range(0, len(self.analyzer_taggs)):
            self.taggs.append(db.selectAnalyzerTag(self.analyzer_taggs[k], flag))
        db.close()

        for i in range(0, len(self.analyzer_taggs)):
            if default_valid_type[i] == "AUTO": # 오로지 default validation_type이 AUTO로 설정 되어 있는 경우에만 진행한다.
                if flag == "OPC":
                    opcmodule = withOPC(self.analyzer_taggs[i], self.taggs[i])
                    dcs_start_signal = opcmodule.getting(self.taggs[i][25], self.taggs[i][13])
                    if dcs_start_signal == 1:
                        alarm_value, fault_value = self.check_alarm_fault(opcmodule, self.taggs[i][25], self.taggs[i][16], self.taggs[i][15])
                        valid_state_value= opcmodule.getting(self.taggs[i][25], self.taggs[i][7])
                        if alarm_value == 1 or fault_value == 1 or valid_state_value == 1:
                            pass
                        else:
                            print("벨리데이션 시작")
                            DCS_validation = Thread(target=opcmodule.start_Validation_preprocess,
                                                    args=(default_valve[i], default_valid_type[i], self.analyzer_taggs[i], "DCS", default_bottle[i]))
                            DCS_validation.start()
                    else:
                        print("시그널 안 들어옴")
                        pass
                elif flag == "MODBUS":
                    modbusmodule = withMODBUS(self.analyzer_taggs[i], self.taggs[i])
                    dcs_start_signal= modbusmodule.getting(self.taggs[i][25], self.taggs[i][13], flag)
                    if dcs_start_signal == 1:
                        alarm_value, fault_value = self.check_alarm_fault(modbusmodule, self.taggs[i][25], self.taggs[i][16], self.taggs[i][15])
                        valid_state_value = opcmodule.getting(self.taggs[i][25], self.taggs[i][7])
                        if alarm_value == 1 or fault_value == 1 or valid_state_value == 1:
                            pass
                        else:
                            DCS_validation = Thread(target=modbusmodule.start_Validation_preprocess,
                                                    args=(default_valve[i], default_valid_type[i], self.analyzer_taggs[i], "DCS", default_bottle[i]))
                            DCS_validation.start()
                    else:
                        pass
            else:
                print("엘스로 빠짐")
                pass