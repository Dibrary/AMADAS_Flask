from lxml import etree
from db_module import *

from modbus_module import *

class read_modbus_process_value:
    def __init__(self, version):
        self.analyzer_taggs = []
        self.taggs = []
        self.version = version
        db = withDB()
        analyzer_taggs = db.selectAllAnalyzer() # 반환 꼴은 ((analyzer_정보, analyzer_정보, analyzer_정보)) 꼴
        for i in range(0, len(analyzer_taggs)):
            self.analyzer_taggs.append(analyzer_taggs[i][0])
        for k in range(0, len(self.analyzer_taggs)):
            self.taggs.append(db.selectAnalyzerTag(self.analyzer_taggs[k], "MODBUS"))
        db.close()
        root = (etree.parse("opc_modbus_db_ip.xml")).getroot()
        for i in root.iter("slave"):
            self.dcsip = (i.findtext("dcsip"))[:13]   # dcs ip
            self.dcsport = (i.findtext("dcsip"))[14:] # dcs port
            self.gcip = (i.findtext("gcip"))[:13]   # gc ip
            self.gcport = (i.findtext("gcip"))[14:] # gc port

        self.save_process_value_modbus()

    def check_flag(self): # 단순 flag 체크 용도.
        flag = ''
        if self.version == 2 or self.version == 4:
            flag = "GC"
        elif self.version == 3:
            flag = "DCS"
        return flag

    def save_process_value_modbus(self): # 반복문을 통해서, 값을 getting메서드로 가져오고, 그 값을 insertProcessValueRealtime메서드로 DB에 저장한다.
        db = withDB()
        for i in range(0, len(self.taggs)):
            modbusmodule = withMODBUS(self.analyzer_taggs[i], self.taggs[i])
            in_valid_value = modbusmodule.getting(self.taggs[i], self.taggs[i][7])
            alarm_value, fault_value = modbusmodule.check_alarm_fault(self.taggs[i][25], self.taggs[i][16], self.taggs[i][15])
            if alarm_value == 1 or fault_value == 1 or in_valid_value == 1: # alarm, fault 둘 중 하나라도 1이라면, 값 저장 안함.
                pass
            elif alarm_value == 0 and fault_value == 0 and in_valid_value == 0:
                flag = self.check_flag()
                process_taggs = db.selectProcessTagToInfinitByTag(self.analyzer_taggs[i], "MODBUS") # 꺼내온 데이터는 (('5',),('6',),('7',))
                for k in range(0, len(process_taggs)):
                    value = modbusmodule.getting(self.taggs[i][25], int(process_taggs[k][0]), flag)
                    db.insertProcessValueRealtime(self.analyzer_taggs[i], int(process_taggs[k][0]), value, "MODBUS") # ana_tag, process_tag, process_value
        db.close()

