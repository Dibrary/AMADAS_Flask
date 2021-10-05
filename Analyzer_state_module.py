from lxml import etree

from db_module import *
from opc_controller import *
from modbus_controller import *

def Analyzer_state_logs(): # 실시간으로 analyzer state를 읽는 작업만 한다.
    db = withDB()
    analyzer_state_tag = db.selectAnalyzerEventTag() # analyzer들의 network 데이터가 반환된다.
    db.close()

    for i in range(0, len(analyzer_state_tag)):
        if analyzer_state_tag[i][0] == "MODBUS": # network데이터가 MODBUS인 경우.
            mc = ModbusController(analyzer_state_tag[i][3], analyzer_state_tag[i])
            mc.realtime_Analyzerstate()
        elif analyzer_state_tag[i][0] == "OPC":
            oc = OpcController(analyzer_state_tag[i][3], analyzer_state_tag[i])
            oc.realtime_Analyzerstate()