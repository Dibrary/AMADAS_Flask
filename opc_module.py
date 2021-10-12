import datetime
import time

from abc import *
from lxml import etree
from flask_socketio import SocketIO, send, join_room,leave_room, emit, close_room, rooms, disconnect

from opcua import Client
from lims_module import *
from modbus_module import *
from LIMS_auto_module import *
from db_module import *
from validation_opc_module import *

from VO.lims import LIMS
from VO.report import report
from VO.device import device

global alarm_init, in_valid_init, maint_init
global ana_fault_init, lims_btn_init, lims_db_init, valid_permit_init
global dcs_start_valid_init

db_init = withDB()
length = (db_init.analyzerCount())
house_length = (db_init.houseCount())
db_init.close()

alarm_init = [0]*length[0]
in_valid_init = [0]*length[0]
#maint_init = [0]*length[0]
break_init = [0]*length[0]
ana_fault_init = [0]*length[0]
lims_btn_init = [0]*length[0]
lims_db_init = [0]*length[0]
valid_permit_init = [0]*length[0]
dcs_start_valid_init = [0]*length[0]


class withOPC:
    def __init__(self, object_tag, taggs):
        self.object_tag = object_tag
        self.taggs = taggs
        root = (etree.parse("opc_modbus_db_ip.xml")).getroot()
        for i in root.iter("server"):   self.url = i.findtext("url")
        for j in root.iter("address"):  self.version = int(j.findtext("version"))

        self.dbmodule = withDB()
        if self.version == 2:
            # object_tag로 House가 들어온다...
            modbus_taggs = self.dbmodule.selectAnalyzerTag(self.object_tag, "MODBUS") # tag 첫 번째에 db의 데이터 no있다.
            if modbus_taggs != None:
                self.modbus_taggs = modbus_taggs
                self.index_m = self.modbus_taggs[25]
                self.modbusmodule = withMODBUS(object_tag, self.modbus_taggs)
            else:
                pass
        else:
            pass

    def opcconnect(self):
        self.opcclient = Client(self.url)
        self.opcclient.connect()

    def opcclose(self):
        self.opcclient.disconnect()

    def set_to_on(self, index, tag):
        self.opcconnect()
        node_object = self.opcclient.get_node("ns=" + str(index) + ";s=" + tag)
        node_object.set_value(1)
        self.opcclose()

    def set_to_off(self, index, tag):
        self.opcconnect()
        node_object = self.opcclient.get_node("ns=" + str(index) + ";s=" + tag)
        node_object.set_value(0)
        self.opcclose()

    def getting(self, index, tag):
        self.opcconnect()
        node_object = self.opcclient.get_node("ns=" + str(index) + ";s=" + tag)
        value = node_object.get_value()
        self.opcclose()
        return value

    def read_Analyzer_state(self):
        result = 0
        if self.version == 1:
            index = self.taggs[25]
            tag_list = [self.taggs[2], self.taggs[16], self.taggs[7], self.taggs[3], self.taggs[15],
                        self.taggs[6]]  # normal, alarm, valid, maint, fault, break 순서
            for i in range(0, len(tag_list)):
                value = self.getting(index, tag_list[i]) # opc에서 값 가져온다.
                if value == 1: result = i
        elif self.version == 2:
            opc_index = self.taggs[25]
            tag_list = [self.taggs[2], self.taggs[7], self.taggs[3], self.taggs[6]]
            # normal, valid, maint, break 순서
            state_values = []
            for i in range(0, len(tag_list)):
                state_values.append(int(self.getting(opc_index, tag_list[i]))) # opc에서 값 가져온다.

            alarm, fault = self.modbusmodule.check_alarm_fault(self.index_m, self.modbus_taggs[16], self.modbus_taggs[15])  # index, alarm, fault 순서
            state_values.insert(1, int(alarm))
            state_values.insert(4, int(fault))
            for k in range(0, len(state_values)):
                if state_values[k] == 1: result = k
        return result

    def check_dcs_permit(self):
        global valid_permit_init
        ana_no = (self.dbmodule.selectAnalyzerNoByTag(self.object_tag))[2]
        valid_perm_tag = self.taggs[11]
        index = self.taggs[25]
        try:
            permit = self.getting(index, valid_perm_tag)
            result = ''
            if permit == 0:
                result = "NotOK"
                valid_permit_init[ana_no-1] = 0
            elif permit == 1 and valid_permit_init[ana_no-1] != 1:
                result = "OK"
                valid_permit_init[ana_no-1] = 1
            return result
        except:
            self.dbmodule.insertExceptLogByTag(self.object_tag, "check_dcs_permit")
            return "ERROR"

    def check_dcs_start_validation(self):
        global dcs_start_valid_init
        ana_no = (self.dbmodule.selectAnalyzerNoByTag(self.object_tag))[2]
        dcs_start_tag = self.taggs[13]
        index = self.taggs[25]
        try:
            dcs_start_value = self.getting(index, dcs_start_tag)
            result = ''
            if dcs_start_value == 0:
                result = "NotOK"
                dcs_start_valid_init[ana_no-1] = 0
            elif dcs_start_value == 1 and dcs_start_valid_init[ana_no-1] != 1:
                result = "OK"
                dcs_start_valid_init[ana_no-1] = 1
            return result
        except:
            self.dbmodule.insertExceptLogByTag(self.object_tag, "check_dcs_start_validation")
            return "ERROR"

    def request_Validation(self, bottle_tag):
        expire_date = self.dbmodule.selectBottleExpireByTag(self.object_tag, bottle_tag)
        if expire_date[0] > datetime.datetime.now():
            result = None
            valid_req_tag = self.taggs[10]
            valid_perm_tag = self.taggs[11]
            index = self.taggs[25]

            self.set_to_on(index, valid_req_tag)
            permit = self.getting(index, valid_perm_tag)

            if permit == 0:
                result = "NotOK"
            elif permit == 1:
                result = "OK"
            return result
        elif expire_date[0] < datetime.datetime.now():  # 참조병 만료 기간이 지났으면 못 한다.
            return "REFER"

    def request_Validation_scheduler(self):
        valid_req_tag = self.taggs[10]
        index = self.taggs[25]
        self.set_to_on(index, valid_req_tag)
        time.sleep(0.5)
        self.set_to_off(index, valid_req_tag)

    def request_Maintenance(self):
        result = None
        valid_req_tag = self.taggs[4]
        valid_perm_tag = self.taggs[5]
        index = self.taggs[25]
        try:
            self.set_to_on(index, valid_req_tag)
            permit = self.getting(index, valid_perm_tag)

            if permit == 0:
                result = "NotOK"
            elif permit == 1:
                result = "OK"
            return result
        except:
            self.dbmodule.insertExceptLogByTag(self.object_tag, "request_maintenance")
            return "ERROR"

    def start_Maintenance(self, user_id):
        result = None
        in_maint_tag = self.taggs[3]
        index = self.taggs[25]
        try:
            self.set_to_on(index, in_maint_tag)
            in_maint_value = self.getting(index, in_maint_tag)
            if in_maint_value == 0:
                result = "NotOK"
            elif in_maint_value == 1:
                result = "OK"
                self.dbmodule.insertEventStartLog(self.object_tag, "MAINT", in_maint_tag, user_id)
            return result
        except:
            self.dbmodule.insertExceptLogByTag(self.object_tag, "start_maintenance")
            return "ERROR"

    def stop_Maintenance(self, user_id):
        result = None
        in_maint_tag = self.taggs[3]
        index = self.taggs[25]
        try:
            self.set_to_off(index, in_maint_tag)
            in_maint_value = self.getting(index, in_maint_tag)
            if in_maint_value == 0:
                result = "OK"
                self.dbmodule.insertEventStopLog(self.object_tag, "MAINT", in_maint_tag, user_id)
            elif in_maint_value == 1:
                result = "NotOK"
            return result
        except:
            self.dbmodule.insertExceptLogByTag(self.object_tag, "stop_maintenance")
            return "ERROR"

    def calibration(self, user_id):
        result = ''
        try:
            if self.version == 1:
                calib_tag = self.taggs[14]
                index = self.taggs[25]

                self.set_to_on(index, calib_tag)
                calib_value = self.getting(index, calib_tag)
                if calib_value == 0:
                    result = "NotOK"
                elif calib_value == 1:
                    result = "OK"
                    self.dbmodule.insertEventStartLog(self.object_tag, "CALIB", calib_tag, user_id)
            elif self.version == 2:
                result = self.modbusmodule.calibration(user_id)
            return result
        except:
            self.dbmodule.insertExceptLogByTag(self.object_tag, "calibration")
            return "ERROR"

    def lims_Comparison(self, lims_data):
        lm = lims_module(self.object_tag,
                         lims_data.get_process_tag(),
                         lims_data.get_start_datetime(),
                         lims_data.get_end_datetime(),
                         lims_data.get_lims_value())
        result = lm.compare_process_value()
        return result

    def check_alarm_fault(self, index, alarm_tag, fault_tag):
        alarm_value, fault_value = 0, 0
        try:
            if self.version == 1:
                alarm_value = self.getting(index, alarm_tag)
                fault_value = self.getting(index, fault_tag)
            elif self.version == 2:
                alarm_value, fault_value = self.modbusmodule.check_alarm_fault(self.index_m, self.modbus_taggs[16],
                                                                               self.modbus_taggs[15])
            return alarm_value, fault_value
        except:
            self.dbmodule.insertExceptLogByTag(self.object_tag, "check_alarm_fault")
            return 1, 1

    def check_valve_on_pulse(self, index, valve_tag):  # version 2 라면 modbus_tag에 해당하는 valve_tag가 들어올 것.
        valid_state_tag = self.taggs[7]
        start_valid_tag = self.taggs[8]
        try:
            if self.version == 1:
                #            self.set_to_on(index, valve_tag) # valve ON
                self.set_to_on(index, start_valid_tag)  # start_validation ON
                time.sleep(0.5)
            #            self.set_to_off(index, valve_tag) # valve OFF
            elif self.version == 2:
                start_valid_tag_m = self.modbus_taggs[8]
                #            self.modbusmodule.set_to_on(self.index_m, valve_tag, "GC") # valve ON
                self.set_to_on(index, start_valid_tag)  # start_validation ON(OPC)
                time.sleep(0.5)
            #            self.modbusmodule.set_to_off(self.index_m, valve_tag, "GC") # valve OFF
            self.set_to_off(index, start_valid_tag)
            self.set_to_on(index, valid_state_tag)  # in_validation ON
            print(valid_state_tag)
            print("in_validation ON")
        except:
            self.dbmodule.insertExceptLogByTag(self.object_tag, "check_valve_on_pulse")


    def check_valve_on_hold(self, index, valve_tag):
        valid_state_tag = self.taggs[7]
        start_valid_tag = self.taggs[8]
        try:
            if self.version == 1:
                #            self.set_to_on(index, valve_tag) # valve ON
                self.set_to_on(index, start_valid_tag)  # start_validation ON
            elif self.version == 2:
                start_valid_tag_m = self.modbus_taggs[8]
                #            self.modbusmodule.set_to_on(self.index_m, valve_tag, "GC") # valve ON
                self.set_to_on(index, start_valid_tag)  # start_validation ON(OPC)
            self.set_to_on(index, valid_state_tag)  # in_validation ON
            print(valid_state_tag)
            print("in_validation ON")
        except:
            self.dbmodule.insertExceptLogByTag(self.object_tag, "check_valve_on_hold")

    def check_valve_off_pulse(self, index, valve_tag, delay_time):
        valid_state_tag, start_valid_tag, stop_valid_tag = self.taggs[7], self.taggs[8], self.taggs[9]
        try:
            if self.version == 1:
                #            self.set_to_on(index, valve_tag) # valve ON
                self.set_to_on(index, stop_valid_tag)  # stop validation ON
                time.sleep(0.5)
                #            self.set_to_off(index, valve_tag) # valve OFF
                self.set_to_off(index, stop_valid_tag)  # stop validation OFF
                time.sleep(delay_time.seconds)  # 벨브 닫고 시간이 어느정도 흐른 뒤에 start_validation이 꺼지고, end_validation 트리거 및 in_validation 신호 꺼짐.
                self.set_to_off(index, start_valid_tag)  # start_validation OFF
            elif self.version == 2:
                start_valid_tag_m, stop_valid_tag_m = self.modbus_taggs[8], self.modbus_taggs[9]
                #            self.modbusmodule.set_to_on(self.index_m, valve_tag, "GC") # valve ON
                self.modbusmodule.set_to_on(self.index_m, stop_valid_tag_m, "GC")  # stop validation ON
                time.sleep(0.5)
                #            self.modbusmodule.set_to_off(self.index_m, valve_tag, "GC") # valve OFF
                self.modbusmodule.set_to_off(self.index_m, stop_valid_tag_m, "GC")  # stop validation OFF
                time.sleep(delay_time.seconds)
                self.set_to_off(index, start_valid_tag)  # start_validation OFF(OPC)
            self.set_to_off(index, valid_state_tag)  # in_validation OFF
        except:
            self.dbmodule.insertExceptLogByTag(self.object_tag, "check_valve_off_pulse")

    def check_valve_off_hold(self, index, valve_tag, delay_time):
        valid_state_tag, start_valid_tag, stop_valid_tag = self.taggs[7], self.taggs[8], self.taggs[9]
        try:
            if self.version == 1:
                #            self.set_to_off(index, valve_tag) # valve OFF
                self.set_to_on(index, stop_valid_tag)  # end_validation ON
                time.sleep(delay_time.seconds)
                self.set_to_off(index, stop_valid_tag)  # end_validation OFF
                self.set_to_off(index, start_valid_tag)  # start_validation OFF
            elif self.version == 2:
                start_valid_tag_m, stop_valid_tag_m = self.modbus_taggs[8], self.modbus_taggs[9]
                #            self.modbusmodule.set_to_off(self.index_m, valve_tag, "GC") # valve OFF
                self.modbusmodule.set_to_on(self.index_m, stop_valid_tag_m, "GC")  # stop validation ON
                time.sleep(0.5)
                self.modbusmodule.set_to_off(self.index_m, stop_valid_tag_m, "GC")  # stop validation OFF
                time.sleep(delay_time.seconds)
                self.set_to_off(index, start_valid_tag)  # start_validation OFF(OPC)
            self.set_to_off(index, valid_state_tag)  # in_validation OFF
        except:
            self.dbmodule.insertExceptLogByTag(self.object_tag, "check_valve_off_hold")

    def start_Validation_preprocess(self, valve_signal: str, order: str, ana_tag: str, user_id: str, bottle_tag: str):
        result = None
        valve_tag = ''
        if self.version == 1:
            valve_tag = self.dbmodule.selectBottleValve(ana_tag, bottle_tag, "OPC")
        elif self.version == 2:
            valve_tag = self.dbmodule.selectBottleValve(ana_tag, bottle_tag, "MODBUS")

        print(self.version, "셀프버전")
        print(self.taggs, "태그스")
        index = self.taggs[25]
        alarm_tag, fault_tag = self.taggs[16], self.taggs[15]
        alarm, fault = self.check_alarm_fault(index, alarm_tag, fault_tag)
        if (int(alarm) + int(fault)) >= 1:
            result = "Alarm or Fault before Purge"
        else:
            if valve_signal == "PULSE":
                self.check_valve_on_pulse(index, valve_tag)

                if self.version == 1:
                    validation = Validation()
                    self.opcconnect()
                    result = validation.start_Validation(self.opcclient, order, ana_tag, bottle_tag, user_id)
                    self.opcclose()
                elif self.version == 2:
                    validation = Validation_m()
                    self.modbusmodule.modbusconnect()
                    result = validation.start_Validation(self.modbusmodule.client2, order, ana_tag, bottle_tag, user_id)
                    self.modbusmodule.modbusclose()

                delay_time = datetime.timedelta(seconds=10)
                self.check_valve_off_pulse(index, valve_tag, delay_time)
            elif valve_signal == "HOLD":
                self.check_valve_on_hold(index, valve_tag)

                if self.version == 1:
                    validation = Validation()
                    self.opcconnect()
                    result = validation.start_Validation(self.opcclient, order, ana_tag, bottle_tag, user_id)
                    self.opcclose()
                elif self.version == 2:
                    validation = Validation_m()
                    self.modbusmodule.modbusconnect()
                    result = validation.start_Validation(self.modbusmodule.client2, order, ana_tag, bottle_tag, user_id)
                    self.modbusmodule.modbusclose()
                delay_time = datetime.timedelta(seconds=10)
                self.check_valve_off_hold(index, valve_tag, delay_time)
        return result

    def change_semi_auto_tag(self, user_id):  # semi_auto값 저장하라고 opc값을 trigger시키는 함수.
        try:
            if self.version == 1:
                index = self.taggs[25]
                semi_auto_tag = self.taggs[27]
                self.set_to_on(index, semi_auto_tag)
                time.sleep(1.0)
                self.set_to_off(index, semi_auto_tag)
            elif self.version == 2:
                semi_auto_tag = self.modbus_taggs[27]
                self.modbusmodule.set_to_on(self.index_m, semi_auto_tag, "GC")
                time.sleep(1.0)
                self.modbusmodule.set_to_off(self.index_m, semi_auto_tag, "GC")
            print("semi auto signal triggered")
            return "OK"
        except:
            self.dbmodule.insertExceptLogByTag(self.object_tag, "change_semi_auto_tag")
            return "NotOK"

    def LIMS_recognize_from_button(self, index: int):
        pass

    #        value = self.getting(index, self.taggs)
    #        if value == 1:
    #            if lims_btn_init[index-1] == value:
    #                pass
    #            elif lims_btn_init[index-1] != value:
    #                valid_tag = self.dbmodule.selectProcessTagByTag(self.object_tag)
    #                result = []
    #                for i in range(0, len(valid_tag)): # tag 갯수 만큼 순회 하고, 값을 process에서 가져온다.
    #                    result.append(self.getting(index, valid_tag[i][0]))
    #                self.dbmodule.save_LIMS_data(self.object_tag, result)
    #        elif value == 0:
    #            if lims_btn_init[index-1] == 1:
    #                lims_btn_init[index-1] = 0
    #            else:
    #                pass

    def LIMS_recognize_from_limsDB(self, index: int):
        value = self.getting(index, self.taggs)
        if value == 1:
            if lims_db_init[index - 1] == value:
                pass
            elif lims_db_init[index - 1] != value:
                AL = Auto_LIMS_Data_Save()
                AL.read_and_save_lims()
        elif value == 0:
            if lims_db_init[index - 1] == 1:
                lims_db_init[index - 1] = 0
            else:
                pass

    def Analyzerstate_divider(self, state, index, ana_tag, event_type, tag): # DB에 analyzer state를 기록한다.
        if state == "START":
            self.dbmodule.insertEventStartLog(ana_tag, event_type, tag)
        elif state == "STOP":
            self.dbmodule.insertEventStopLog(ana_tag, event_type, tag)

    def realtime_Analyzerstate(self): # analyzer state에 대한 변화가 감지되면, 그 내용을 DB에 기록하는 함수로 넘어간다.
        global in_valid_init
        global ana_fault_init
        global alarm_init
        global break_init
        break_value = self.getting(self.taggs[1], self.taggs[6])
        valid_value = self.getting(self.taggs[1], self.taggs[7])
        alarm_value, fault_value = 0, 0
        if self.version == 1:
            alarm_value = self.getting(self.taggs[1], self.taggs[8])
            fault_value = self.getting(self.taggs[1], self.taggs[9])
        elif self.version == 2:
            alarm_value = self.modbusmodule.getting(self.index_m, self.modbus_taggs[16], "GC")
            fault_value = self.modbusmodule.getting(self.index_m, self.modbus_taggs[15], "GC")

        if valid_value != in_valid_init[self.taggs[1] - 1]:
            in_valid_init[self.taggs[1] - 1] = valid_value
            valid_tag_state = ("START" if valid_value == 1 else "STOP")
            self.Analyzerstate_divider(valid_tag_state, self.taggs[4], self.taggs[3], "VALID", self.taggs[7])

        if fault_value != ana_fault_init[self.taggs[1] - 1]:
            ana_fault_init[self.taggs[1] - 1] = fault_value
            fault_tag_state = ("START" if fault_value == 1 else "STOP")
            self.Analyzerstate_divider(fault_tag_state, self.taggs[4], self.taggs[3], "FAULT", self.taggs[9])

        if alarm_value != alarm_init[self.taggs[1] - 1]:
            alarm_init[self.taggs[1] - 1] = alarm_value
            alarm_tag_state = ("START" if alarm_value == 1 else "STOP")
            self.Analyzerstate_divider(alarm_tag_state, self.taggs[4], self.taggs[3], "ALARM", self.taggs[8])

        if break_value != break_init[self.taggs[1] - 1]:
            break_init[self.taggs[1] - 1] = break_value
            break_tag_state = ("START" if break_value == 1 else "STOP")
            self.Analyzerstate_divider(break_tag_state, self.taggs[4], self.taggs[3], "BREAK", self.taggs[6])