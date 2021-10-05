from lxml import etree
from db_module import *
from decimal import *

from opc_module import *

class read_opc_process_value:
    def __init__(self, version):
        self.analyzer_taggs = []
        self.taggs = []
        self.version = version
        db = withDB()
        analyzer_taggs = db.selectAllAnalyzer() # 반환 꼴은 ((analyzer_정보, analyzer_정보, analyzer_정보)) 꼴
        for i in range(0, len(analyzer_taggs)):
            self.analyzer_taggs.append(analyzer_taggs[i][0])
        for k in range(0, len(self.analyzer_taggs)):
            self.taggs.append(db.selectAnalyzerTag(self.analyzer_taggs[k], "OPC"))
        db.close()
        root = (etree.parse("opc_modbus_db_ip.xml")).getroot()
        for i in root.iter("server"):   self.url = i.findtext("url")
        for j in root.iter("address"):  self.version = int(j.findtext("version"))
        self.save_process_value_opc()

    def save_process_value_opc(self): # 반복문을 통해서, 값을 getting메서드로 가져오고, 그 값을 insertProcessValueRealtime메서드로 DB에 저장한다.
        db = withDB()
        for i in range(0, len(self.taggs)):
            opcmodule = withOPC(self.analyzer_taggs[i], self.taggs[i])
            in_valid_value = opcmodule.getting(self.taggs[i][25], self.taggs[i][7])
            alarm_value, fault_value = opcmodule.check_alarm_fault(self.taggs[i][25], self.taggs[i][16], self.taggs[i][15])
            if alarm_value == 1 or fault_value == 1 or in_valid_value == 1: # alarm, fault 둘 중 하나라도 1이라면, 값 저장 안함.
                pass
            elif alarm_value == 0 and fault_value == 0 and in_valid_value == 0:
                process_taggs = db.selectProcessTagToInfinitByTag(self.analyzer_taggs[i], "OPC") # 꺼내온 데이터는 (('5',),('6',),('7',))
                for k in range(0, len(process_taggs)):
                    value = opcmodule.getting(self.taggs[i][25], process_taggs[k][0])
                    db.insertProcessValueRealtime(self.analyzer_taggs[i], process_taggs[k][0], value, "OPC") # ana_tag, process_tag, process_value
        db.close()
