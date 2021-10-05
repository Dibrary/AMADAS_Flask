from lxml import etree

from db_module import *
from opc_controller import *
from modbus_controller import *


def Lims_trigger(): # LIMS 값으로 저장할 목적으로 사용자가 신호를 보내면, 이 함수에서 network node 값을 읽어서 동작한다.
    db = withDB()
    analyzertag_network = db.selectAnalyzerTagAndLIMS()
    db.close()

    for i in range(0, len(analyzertag_network)):
        if analyzertag_network[i][1] == "MODBUS":
            mc = ModbusController(analyzertag_network[i][0], analyzertag_network[i][2])
            mc.LIMS_recognize_from_button(analyzertag_network[i][3])

        elif analyzertag_network[i][1] == "OPC":
            oc = OpcController(analyzertag_network[i][0], analyzertag_network[i][2])
            oc.LIMS_recognize_from_button(analyzertag_network[i][3])


def Lims_db_data():
    db = withDB()
    analyzertag_network = db.selectAnalyzerTagAndLIMS()
    db.close()

    for i in range(0, len(analyzertag_network)):
        if analyzertag_network[i][1] == "MODBUS":
            mc = ModbusController(analyzertag_network[i][0], analyzertag_network[i][2])
            mc.LIMS_recognize_from_limsDB(analyzertag_network[i][3])

        elif analyzertag_network[i][1] == "OPC":
            oc = OpcController(analyzertag_network[i][0], analyzertag_network[i][2])
            oc.LIMS_recognize_from_limsDB(analyzertag_network[i][3])