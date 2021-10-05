import datetime
import time
from lxml import etree
from pymodbus.client.sync import ModbusTcpClient

from db_module import *
from validation_modbus_module import *
from lims_module import *
from LIMS_auto_module import *

global alarm_init_m, in_valid_init_m, maint_init_m, ana_fault_init_m
global lims_btn_init_m, lims_db_init_m, valid_permit_init_m
global dcs_start_valid_init_m

db_init_m = withDB()
length = (db_init_m.analyzerCount())
house_length = (db_init_m.houseCount())
db_init_m.close()

alarm_init_m = [0]*length[0]
in_valid_init_m = [0]*length[0]
break_init_m = [0]*length[0]
ana_fault_init_m = [0]*length[0]
lims_btn_init_m = [0]*length[0]
lims_db_init_m = [0]*length[0]
valid_permit_init_m = [0]*length[0]
dcs_start_valid_init_m = [0]*length[0]


class withMODBUS:
    ip: str
    dbmodule: object
    object_tag: str
    taggs: list

    def __init__(self, object_tag, taggs):
        self.object_tag = object_tag
        self.taggs = taggs
        root = (etree.parse("opc_modbus_db_ip.xml")).getroot()
        for i in root.iter("slave"):
            self.dcsip = (i.findtext("dcsip"))[:13]   # dcs ip
            self.dcsport = (i.findtext("dcsip"))[14:] # dcs port
            self.gcip = (i.findtext("gcip"))[:13]   # gc ip
            self.gcport = (i.findtext("gcip"))[14:] # gc port
        for j in root.iter("address"):  self.version = int(j.findtext("version"))
        self.dbmodule = withDB()

    def modbus_ip_Parse(self):
        return self.ip

    def modbusconnect(self): # modbus ip주소에 접속을 시도한다.
        if self.version == 2:
            self.client2 = ModbusTcpClient(self.gcip, self.gcport)
        elif self.version == 3:
            self.client = ModbusTcpClient(self.dcsip, self.dcsport)
        elif self.version == 4:
            self.client = ModbusTcpClient(self.dcsip, self.dcsport)
            self.client2 = ModbusTcpClient(self.gcip, self.gcport)

    def modbusclose(self): # modbus 접속을 끊는다.
        if self.version == 2:
            self.client2.close()
        elif self.version == 3:
            self.client.close()
        elif self.version == 4:
            self.client.close()
            self.client2.close()

    def set_to_on(self, index, tag, flag): # modbus의 address값을 1로 바꾼다. (coil에 대해서만 동작)
        self.modbusconnect()
        if flag == "DCS":
            self.client.write_coil((int(tag) + int(index)), True)
        elif flag == "GC":
            self.client2.write_coil((int(tag) + int(index)), True)
        self.modbusclose()

    def set_to_off(self, index, tag, flag): # modbus의 address값을 0로 바꾼다. (coil에 대해서만 동작)
        self.modbusconnect()
        if flag == "DCS":
            self.client.write_coil((int(tag) + int(index)), False)
        elif flag == "GC":
            self.client2.write_coil((int(tag) + int(index)), False)
        self.modbusclose()

    def digital_input_getting(self, index, tag, flag): # 1로 시작하는 address에서 상태값을 읽어온다.
        value = 0
        self.modbusconnect()
        if flag == "DCS":
            value = int((self.client.read_discrete_inputs(int(tag) + int(index))).bits[0])
        elif flag == "GC":
            value = int((self.client2.read_discrete_inputs(int(tag) + int(index))).bits[0])
        self.modbusclose()
        return value

    def getting(self, index, tag, flag): # 이 기능은 coil 값만 읽는 기능
        value = 0
        self.modbusconnect()
        if flag == "DCS":
            value = int((self.client.read_coils(int(tag) + int(index))).bits[0])
        elif flag == "GC":
            value = int((self.client2.read_coils(int(tag) + int(index))).bits[0])
        self.modbusclose()
        return value

    def read_Analyzer_state(self): # analyzer 상태를 숫자로 표현해서 반환한다.
        index = self.taggs[25]
        result = 0
        if self.version == 3:
            tag_list = [self.taggs[2], self.taggs[16], self.taggs[7], self.taggs[3], self.taggs[15],
                        self.taggs[6]]  # normal, alarm, valid, maint, fault, break 순서
            for i in range(0, len(tag_list)):
                value = self.getting(index, tag_list[i], "DCS")
                if value == 1:  result = i
        elif self.version == 4:
            tag_list = [self.taggs[2], self.taggs[7], self.taggs[3], self.taggs[6]]  # normal, valid, maint, break 순서
            state_list = []
            for i in range(0, len(tag_list)):
                state_list.append(int(self.getting(index, tag_list[i], "DCS")))
            alarm_value, fault_value = self.check_alarm_fault(index, self.taggs[16], self.taggs[15])
            state_list.insert(1, int(alarm_value))
            state_list.insert(4, int(fault_value))

            for k in range(0, len(state_list)):
                if state_list[k] == 1: result = k
        return result

    def check_dcs_permit(self): # dcs가 permit 신호를 보냈는지를 확인한다. (permit이 1인지 0인지 확인)
        global valid_permit_init_m
        ana_no = (self.dbmodule.selectAnalyzerNoByTag(self.object_tag))[2]
        valid_perm_tag = self.taggs[11]
        index = self.taggs[25]
        permit = self.getting(index, valid_perm_tag, "DCS")
        result = ''
        if permit == 0:
            result = "NotOK"
            valid_permit_init_m[ana_no - 1] = 0
        elif permit == 1 and valid_permit_init_m[ana_no - 1] != 1:
            result = "OK"
            valid_permit_init_m[ana_no - 1] = 1 # 무한루프 동작이라서, 1로 트리거 된 상태를 계속 읽지 못하게 막으려고 전역변수 설정함.
        return result

    def check_dcs_start_validation(self): # dcs_start_validation의 address가 트리거가 되었는지 확인한다.
        global dcs_start_valid_init_m
        ana_no = (self.dbmodule.selectAnalyzerNoByTag(self.object_tag))[2]
        dcs_start_tag = self.taggs[13]
        index = self.taggs[25]
        dcs_start_value = self.getting(index, dcs_start_tag, "DCS")
        result = ''
        if dcs_start_value == 0: # 1로 트리거 안됨
            result = "NotOK"
            dcs_start_valid_init_m[ana_no - 1] = 0
        elif dcs_start_value == 1 and dcs_start_valid_init_m[ana_no - 1] != 1: # 1로 트리거 됨.
            result = "OK"
            dcs_start_valid_init_m[ana_no - 1] = 1 # 무한루프 동작이라서, 1로 트리거 된 상태를 계속 읽지 못하게 막으려고 전역변수 설정함.
        return result

    def request_Validation(self, bottle_tag): # validation request에 해당되는 address의 값을 1로 트리거 시킨다.
        expire_date = self.dbmodule.selectBottleExpireByTag(self.object_tag, bottle_tag)
        if expire_date[0] > datetime.datetime.now():
            result = None
            valid_req_tag = self.taggs[10]
            valid_perm_tag = self.taggs[11]
            index = self.taggs[25]
            self.set_to_on(index, valid_req_tag, "DCS") # 여기서 1로 트리거 하고,
            permit = self.getting(index, valid_perm_tag, "DCS") # validation permit값을 곧바로 읽는다.

            if permit == 0: # DCS에서 permit 신호가 안 내려온 것,
                result = "NotOK"
            elif permit == 1: # DCS에서 permit 신호가 내려온 것.
                result = "OK"
            return result
        elif expire_date[0] < datetime.datetime.now():
            return "REFER"

    def request_Validation_scheduler(self): # scheduler에 저장된 시간이 되면, validation request를 요청한다.
        valid_req_tag = self.taggs[10]
        index = self.taggs[25]
        self.set_to_on(index, valid_req_tag)
        time.sleep(0.5)
        self.set_to_off(index, valid_req_tag) # 0.5초의 간격을 두고 트리거가 된다.

    def request_Maintenance(self): # maintenance request에 해당되는 address를 1로 트리거 한다.
        result = None
        maint_req_tag = self.taggs[4]
        maint_perm_tag = self.taggs[5]
        index = self.taggs[25]
        self.set_to_on(index, maint_req_tag, "DCS")

        permit = self.getting(index, maint_perm_tag, "DCS")
        if permit == 0:
            result = "NotOK"
        elif permit == 1:
            result = "OK"
        return result

    def start_Maintenance(self, user_id): # maintenance start에 해당되는 address를 1로 변경한다.
        result = None
        in_maint_tag = self.taggs[3]
        index = self.taggs[25]
        self.set_to_on(index, in_maint_tag, "DCS")
        in_maint_value = self.getting(index, in_maint_tag, "DCS")
        if in_maint_value == 0:
            result = "NotOK"
        elif in_maint_value == 1:
            result = "OK"
            self.dbmodule.insertEventStartLog(self.object_tag, "MAINT", in_maint_tag, user_id)
        return result

    def stop_Maintenance(self, user_id): # maintenance stop에 해당되는 address를 1로 변경한다.
        result = None
        in_maint_tag = self.taggs[3]
        index = self.taggs[25]
        self.set_to_off(index, in_maint_tag, "DCS")
        in_maint_value = self.getting(index, in_maint_tag, "DCS")
        if in_maint_value == 0:
            result = "OK"
            self.dbmodule.insertEventStopLog(self.object_tag, "MAINT", in_maint_tag, user_id)
        elif in_maint_value == 1:
            result = "NotOK"
        return result

    def calibration(self, user_id): # calibration에 해당되는 address를 1로 변경한다.
        result, flag = '', ''
        calib_tag = self.taggs[14]
        index = self.taggs[25]
        if self.version == 2 or self.version == 4:
            flag = "GC"
        elif self.version == 3:
            flag = "DCS"
        self.set_to_on(index, calib_tag, flag)
        calib_value = self.getting(index, calib_tag, flag)
        if calib_value == 0:
            result = "NotOK"
        elif calib_value == 1:
            result = "OK"
            self.dbmodule.insertEventStartLog(self.object_tag, "CALIB", calib_tag, user_id)
        return result

    def lims_Comparison(self, process_tag, start_dt, end_dt, process_value): # lims compare를 수행하는 메서드와 연결
        lm = lims_module(self.object_tag, process_tag, start_dt, end_dt, process_value)
        result = lm.compare_process_value()
        return result

    def check_alarm_fault(self, index, alarm_tag, fault_tag): # alarm과 fault의 address 값을 읽어와서 반환한다.
        flag = ''
        if self.version == 2 or self.version == 4:
            flag = "GC"
        elif self.version == 3:
            flag = "DCS"
        try:
            alarm_value = self.getting(index, alarm_tag, flag)
            fault_value = self.getting(index, fault_tag, flag)
            return alarm_value, fault_value
        except:
            self.dbmodule.insertExceptLogByTag(self.object_tag, "check_alarm_fault")
            return 1, 1

    def check_valve_on_pulse(self, index, valve_tag): # valve를 pulse 방식으로 신호를 보내게 하는 메서드 (invalidation을 켠다)
        valid_state_tag, start_valid_tag, flag = self.taggs[7], self.taggs[8], ''
        if self.version == 3:
            flag = "DCS"
            #            self.set_to_on(index, valve_tag, flag)
            self.set_to_on(index, start_valid_tag, flag)  # start_validation ON
            time.sleep(0.5)
        #            self.set_to_off(index, valve_tag, flag)
        elif self.version == 4:
            flag == "GC"
            #            self.set_to_on(index, valve_tag, flag) # valve ON
            self.set_to_on(index, start_valid_tag, "DCS")  # DCS에도 start_validation ON
            time.sleep(0.5)
        #            self.set_to_off(index, valve_tag, flag) # valve OFF
        self.set_to_on(index, valid_state_tag, "DCS")  # in validation ON

    def check_valve_on_hold(self, index, valve_tag): # valve를 holding 방식으로 신호를 보내게 하는 메서드 (invalidation을 켠다)
        valid_state_tag, start_valid_tag, flag = self.taggs[7], self.taggs[8], ''
        if self.version == 3:
            flag = "DCS"
            #            self.set_to_on(index, valve_tag, flag) # valve ON
            self.set_to_on(index, start_valid_tag, flag)  # start validation ON
        elif self.version == 4:
            flag == "GC"
            #            self.set_to_on(index, valve_tag, flag) # valve ON
            self.set_to_on(index, start_valid_tag, "DCS")  # DCS에도 start validation ON
        self.set_to_on(index, valid_state_tag, "DCS")  # in validation ON

    def check_valve_off_pulse(self, index, valve_tag, delay_time): # valve를 pulse방식으로 신호를 보내게 하는 메서드 (invalidation을 여기서 끈다)
        valid_state_tag, start_valid_tag, stop_valid_tag, flag = self.taggs[7], self.taggs[8], self.taggs[9], ''
        if self.version == 3:
            flag = "DCS"
            #            self.set_to_on(index, valve_tag, flag) # valve ON
            self.set_to_on(index, stop_valid_tag, flag)  # stop_validation ON
            time.sleep(0.5)
            #            self.set_to_off(index, valve_tag, flag) # valve OFF
            self.set_to_off(index, stop_valid_tag, flag)  # stop validation OFF
            time.sleep(delay_time.seconds)
            self.set_to_off(index, start_valid_tag, flag)  # start_validation OFF
        elif self.version == 4:
            flag == "GC"
            #            self.set_to_on(index, valve_tag, flag) # valve ON
            self.set_to_on(index, stop_valid_tag, flag)  # stop validation ON
            time.sleep(0.5)
            #            self.set_to_off(index, valve_tag, flag) # valve OFF
            self.set_to_off(index, stop_valid_tag, flag)  # stop validation OFF
            time.sleep(delay_time.seconds)
            self.set_to_off(index, start_valid_tag, flag)  # start_validation OFF
            self.set_to_off(index, start_valid_tag, "DCS")  # DCS에도 start_validation OFF
        self.set_to_off(index, valid_state_tag, "DCS")  # in_validation OFF

    def check_valve_off_hold(self, index, valve_tag, delay_time): # valve를 holding방식으로 신호를 보내게 하는 메서드 (invalidation을 여기서 끈다)
        valid_state_tag, start_valid_tag, stop_valid_tag, flag = self.taggs[7], self.taggs[8], self.taggs[9], ''
        if self.version == 3:
            flag = "DCS"
            #            self.set_to_off(index, valve_tag, flag) # valve OFF
            self.set_to_on(index, stop_valid_tag, flag)  # stop validation ON
            time.sleep(0.5)
            self.set_to_off(index, stop_valid_tag, flag)  # stop validation OFF
            time.sleep(delay_time.seconds)
            self.set_to_off(index, start_valid_tag, flag)  # start validation OFF
        elif self.version == 4:
            flag == "GC"
            #            self.set_to_off(index, valve_tag, flag) # valve OFF
            self.set_to_on(index, stop_valid_tag, flag)  # stop validation ON
            time.sleep(0.5)
            self.set_to_off(index, stop_valid_tag, flag)  # stop validation OFF
            time.sleep(delay_time.seconds)
            self.set_to_off(index, start_valid_tag, "DCS")  # DCS에도 start validation OFF
        self.set_to_off(index, valid_state_tag, "DCS")  # in validation OFF

    def start_Validation_preprocess(self, valve_signal, order, ana_tag, user_id, bottle_tag): # validation 시작하면 들어오는 메서드다.
        result = None
        valve_tag = self.dbmodule.selectBottleValve(ana_tag, bottle_tag, "MODBUS")
        index, alarm_tag, fault_tag = self.taggs[25], self.taggs[16], self.taggs[15]
        alarm, fault = self.check_alarm_fault(index, alarm_tag, fault_tag) # alarm과 fault를 확인하고,
        if (int(alarm) + int(fault)) >= 1:
            result = "Alarm or Fault before Purge"
        else:
            if valve_signal == "PULSE":
                self.check_valve_on_pulse(index, valve_tag) # pulse 상태에 따라 invalidation및 valve 신호들 보냄.

                validation = Validation_m()
                self.modbusconnect()
                if self.version == 3:
                    result = validation.start_Validation(self.client, order, ana_tag, bottle_tag, user_id) # validation을 시작한다.
                elif self.version == 4:
                    result = validation.start_Validation(self.client2, order, ana_tag, bottle_tag, user_id)
                self.modbusclose()

                delay_time = datetime.timedelta(seconds=10)
                self.check_valve_off_pulse(index, valve_tag, delay_time)
            elif valve_signal == "HOLD":
                self.check_valve_on_hold(index, valve_tag)

                validation = Validation_m()
                self.modbusconnect()
                if self.version == 3:
                    result = validation.start_Validation(self.client, order, ana_tag, bottle_tag, user_id)
                elif self.version == 4:
                    result = validation.start_Validation(self.client2, order, ana_tag, bottle_tag, user_id)
                self.modbusclose()

                delay_time = datetime.timedelta(seconds=10)
                self.check_valve_off_hold(index, valve_tag, delay_time)
        return result

    def change_semi_auto_tag(self, user_id): # semi_auto에 해당되는 address의 값을 1로 트리거 시킨다.
        index, semi_auto_tag, flag = self.taggs[25], self.taggs[27], ''
        if self.version == 3:
            flag = "DCS"
        elif self.version == 4:
            flag = "GC"
        self.set_to_on(index, semi_auto_tag, flag)
        time.sleep(1.0)
        self.set_to_off(index, semi_auto_tag, flag)
        print("semi auto trigger")
        return "OK"

    def LIMS_recognize_from_button(self, index):
        pass

    #        value = self.getting(index, self.taggs)
    #        if value == 1:
    #            if lims_btn_init[index-1] == value:
    #                pass
    #            elif lims_btn_init[index-1] != value:
    #                valid_tag = self.dbmodule.selectProcessTagByTag(self.object_tag)
    #                result = []
    #                for i in range(0, len(valid_tag)):
    #                    result.append(self.getting(index, valid_tag[i][0]))
    #                self.dbmodule.save_LIMS_data(self.object_tag, result)
    #        elif value == 0:
    #            if lims_btn_init[index-1] == 1:
    #                lims_btn_init[index-1] = 0
    #            else:
    #                pass

    def LIMS_recognize_from_limsDB(self, index): # LIMS 에 대한 값을 읽으라는 address 주소 값을 읽는 메서드. 읽으라는 신호가 오면, LIMS DB의 값을 읽는 것.
        value = self.getting(index, self.taggs, "DCS")
        if value == 1: # 1일 경우 읽는다.
            if lims_db_init_m[index - 1] == value:
                pass
            elif lims_db_init_m[index - 1] != value:
                AL = Auto_LIMS_Data_Save()
                AL.read_and_save_lims()
        elif value == 0:
            if lims_db_init_m[index - 1] == 1:
                lims_db_init_m[index - 1] = 0
            else:
                pass

    def Analyzerstate_divider(self, state, index, ana_tag, event_type, tag): # event 기록을 state에 따라 다르게 나눠서 DB 저장 코드로 보낸다.
        if state == "START":
            self.dbmodule.insertEventStartLog(ana_tag, event_type, tag)
        elif state == "STOP":
            self.dbmodule.insertEventStopLog(ana_tag, event_type, tag)

    def realtime_Analyzerstate(self): # analyzer state를 읽고, 기존에 읽어놓은 값과 다른지를 확인한다.
        global in_valid_init_m
        global ana_fault_init_m
        global alarm_init_m
        global break_init_m
        flag = ''
        if self.version == 3:
            flag = "DCS"
        elif self.version == 4:
            flag = "GC"
        break_value = self.getting(self.taggs[2], self.taggs[6], "DCS")
        valid_value = self.getting(self.taggs[2], self.taggs[7], "DCS")
        alarm_value = self.getting(self.taggs[2], self.taggs[8], flag)
        fault_value = self.getting(self.taggs[2], self.taggs[9], flag)

        if valid_value != in_valid_init_m[self.taggs[1] - 1]:
            in_valid_init_m[self.taggs[1] - 1] = valid_value
            valid_tag_state = ("START" if valid_value == 1 else "STOP")
            self.Analyzerstate_divider(valid_tag_state, self.taggs[4], self.taggs[3], "VALID", self.taggs[7])

        if fault_value != ana_fault_init_m[self.taggs[1] - 1]:
            ana_fault_init_m[self.taggs[1] - 1] = fault_value
            fault_tag_state = ("START" if fault_value == 1 else "STOP")
            self.Analyzerstate_divider(fault_tag_state, self.taggs[4], self.taggs[3], "FAULT", self.taggs[9])

        if alarm_value != alarm_init_m[self.taggs[1] - 1]:
            alarm_init_m[self.taggs[1] - 1] = alarm_value
            alarm_tag_state = ("START" if alarm_value == 1 else "STOP")
            self.Analyzerstate_divider(alarm_tag_state, self.taggs[4], self.taggs[3], "ALARM", self.taggs[8])

        if break_value != break_init_m[self.taggs[1] - 1]:
            break_init_m[self.taggs[1] - 1] = break_value
            break_tag_state = ("START" if break_value == 1 else "STOP")
            self.Analyzerstate_divider(break_tag_state, self.taggs[4], self.taggs[3], "BREAK", self.taggs[6])
