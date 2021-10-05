from lxml import etree
import datetime

from db_module import *
from opc_module import *
from opc_controller import *

from modbus_module import *
from modbus_controller import *

def Scheduler_check(): # scheduler를 확인한다. (스레드로 돌기 때문에, 실시간으로 계속 확인한다)
    db = withDB()
    recent_row = db.selectFirstScheduler()
    if recent_row == ():
        db.close()
        print("there is no schedule")
        pass
    else: # 여긴 version이 필요 없다 오롯이 DCS랑만 통신하기 때문.
        if datetime.datetime.now() > recent_row[3]:
            db.deleteFirstScheduler()  # 가장 첫 번째 row 삭제
            network = db.selectAnalyzerNetwork(recent_row[1])  # recent_row[1] = ana_tag
            taggs = db.selectAnalyzerTag(recent_row[1], network) # 네트워크에 맞는 tag를 가져온다.
            db.close()

            valve_signal = "PULSE"  # 임의로 지정 함.
            if network[0] == "MODBUS":
                mc = ModbusController(recent_row[1], taggs, recent_row[2])
                mc.request_validation_scheduler()
            elif network[0] == "OPC":
                oc = OpcController(recent_row[1], taggs, recent_row[2])  # ana_tag, taggs, user_id
                oc.request_validation_scheduler()
        else:
            db.close()
            pass