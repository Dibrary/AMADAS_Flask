from lxml import etree

from process_modbus_module import *
from process_opc_module import *

class read_realtime_process_value: # 실시간으로process value를 저장하는 기능
    def __init__(self):
        root = (etree.parse("opc_modbus_db_ip.xml")).getroot()
        for j in root.iter("address"):
            self.version = int(j.findtext("version"))
        if self.version == 2 or self.version == 3 or self.version == 4:
            self.network = "MODBUS"
        else:
            self.network = "OPC"
        self.read_process_value() # 자체 함수 동작.

    def read_process_value(self): # network 정보에 따라 다르게 넘어간다.
        if self.network == "MODBUS":
            read_modbus_process_value(self.version)
        elif self.network == "OPC":
            read_opc_process_value(self.version)

