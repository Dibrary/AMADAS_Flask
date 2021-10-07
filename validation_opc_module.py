import datetime
import time
from abc import *
from flask_socketio import SocketIO, send
from opcua import Client
import copy

from statistical_module import *
from db_module import *


class Validation_Divider(metaclass=ABCMeta):
    def start_Validation(self, opcclient, valid_type, ana_tag, bottle_tag=None, user_id=None):
        self.process = self.create_process(opcclient, valid_type, ana_tag, bottle_tag, user_id)  # validation type에 따라 맞는 인스턴스 생성
        analyzer_type = self.process.select_analyzer_type(ana_tag)
        node_type, analyzer_node = self.process.select_node_type(ana_tag)
        if analyzer_type == "Batch":
            result = self.process.batch_validation(node_type, ana_tag, user_id)  # validation 과정에서 측정한 값들 전부를 return한다.
        elif analyzer_type == "Continue":
            result = self.process.continue_validation(node_type, ana_tag, user_id)  # validation 과정에서 측정한 값들 전부를 return한다.
        return result

    @abstractmethod
    def create_process(self, valid_type):
        pass

class Validation(Validation_Divider): # valid_type에 따라 validation 인스턴스를 다르게 반환한다.
    def create_process(self, opcclient, valid_type, ana_tag, bottle_tag, user_id):
        process = None
        if valid_type == "AUTO":
            process = Auto_Validation(opcclient, ana_tag, bottle_tag, user_id) # 여기서 validation_module의 클래스 인스턴스가 생성된다.
        elif valid_type == "SEMI_AUTO":
            print("세미오토로 들어옴")
            process = Semi_Auto_Validation(opcclient, ana_tag, bottle_tag, user_id) # 여기서 validation_module의 클래스 인스턴스가 생성된다.
        elif valid_type == "MANUAL":
            process = Manual_Validation(opcclient, ana_tag, bottle_tag, user_id)
        return process


class Validation_Architecture(metaclass=ABCMeta):
    def select_taggs(self, ana_tag): # analyzer_tag로 DB의 taggs를 가져온다.
        db = withDB()
        tag_result = db.selectAnalyzerTagByTag(ana_tag)
        db.close()
        return tag_result

    def select_analyzer_parameter(self, ana_tag, network): # 전달인자를 이용해서 DB에서 parameter(purge_time, check_time, count 등등)값을 가져온다.
        db = withDB()
        parameter = db.selectAnalyzerParameterByTag(ana_tag, network)
        db.close()
        return parameter

    def select_component_parameter(self, ana_tag, bottle_tag): # 전달인자를 이용해서 component(reference_value, wl, cl 등)의 값을 가져온다.
        db = withDB()
        result = db.selectComponentParameterByTag(ana_tag, bottle_tag)
        db.close()
        return result

    def select_validation_taggs(self, ana_tag): # analyzer_tag 데이터로 validation tag를 DB에서 가져온다.
        db = withDB()
        result = db.selectValidationTagByTag(ana_tag)  # validation_tag는 bottle과 관계 없이 고정되어 있다.
        db.close()
        # (('1630AI355A-VV',), ('1630AI355B-VV',), ('1630AI355C-VV',))
        return result

    def select_analyzer_type(self, ana_tag): # analyzer_tag 데이터로 DB에서 analyzer의 validation type을 가져온다.
        db = withDB()
        analyzer_type = db.selectAnalyzerTypeByTag(ana_tag)
        db.close()
        return analyzer_type[0]

    def select_node_type(self, ana_tag): # validation 측정 노드가 단일노드인지, 다중인지 구분
        db = withDB()
        analyzer_node = db.selectAnalyzerNodeByTag(ana_tag)
        db.close()
        if len(analyzer_node) != 1:
            result = "MULTI"
        elif len(analyzer_node) == 1:
            result = "SINGL"
        return result, analyzer_node

    def batch_validation(self, node_type, ana_tag, user_id=None): # batch validation에서, 다중 노드인지, 단일 노드인지 구별해서 인스턴스 반환.
        result = ''
        if node_type == "SINGL":
            result = self.batch_singl_validation(ana_tag, user_id)
        elif node_type == "MULTI":
            result = self.batch_multi_validation(ana_tag, user_id)
        return result

    def continue_validation(self, node_type, ana_tag, user_id=None): # continue에서 다중노드인지, 단일노드인지 구별해서 인스턴스 반환.
        result = ''
        if node_type == "SINGL":
            result = self.continue_singl_validation(ana_tag, user_id)
        elif node_type == "MULTI":
            result = self.continue_multi_validation(ana_tag, user_id)
        return result

    def geting_value(self, tag): # opc node의 값을 가져온다.
        node_object = self.opcclient.get_node("ns=" + str(self.index) + ";s=" + tag)
        value = node_object.get_value()
        return value

    def single_slop_detector(self): # 단일노드의 slop를 확인하는 코드.
        interval_time = 0.3  # x-axis
        critical_value = 9  # y-axis

        first = self.geting_value(self.validation_taggs[0][0])
        time.sleep(interval_time)
        second = self.geting_value(self.validation_taggs[0][0])
        if abs(second - first) >= critical_value:
            return False
        else:
            return True

    def multi_slop_detector(self): # 다중노드의 slop를 확인하는 코드.
        interval_time = 0.3
        critical_value = 9

        slop = []
        for i in range(0, len(self.validation_taggs)):
            first = self.geting_value(self.validation_taggs[i][0])
            time.sleep(interval_time)
            second = self.geting_value(self.validation_taggs[i][0])
            slop.append(abs(second - first))
        if max(slop) >= critical_value:
            return False
        else:
            return True

    def come_read_recognize(self): # come_read 신호를 감지하는 코드
        value = self.geting_value(self.come_read_tag)
        return value

    def semi_auto_recognize(self): # semi_auto 신호를 감지하는 코드
        value = self.geting_value(self.semi_auto_button_tag)
        return value

    def calculate_time_interval(self): # continue일 경우 각 측정의 interval time을 계산하는 코드다.
        time_list = []
        now = datetime.datetime.now()
        for i in range(0, self.count):
            temp = now + self.parameter[5]
            time_list.append(temp)
            now = temp
        return time_list

    def check_DCS(self, user_id, valid_value, validation_taggs, ana_tag): # DCS_start_validation으로 시작된 validation이면, browser로 message 전송하지 않는다.
        if user_id == "DCS":
            pass
        else:
            to_client = dict()
            to_client['message'] = valid_value
            to_client['nodes'] = validation_taggs
            to_client['type'] = ana_tag
            send(to_client, broadcast=True)

    @abstractmethod
    def batch_singl_validation(self, ana_tag, user_id):
        pass

    @abstractmethod
    def batch_multi_validation(self, ana_tag, user_id):
        pass

    @abstractmethod
    def continue_singl_validation(self, ana_tag, user_id):
        pass

    @abstractmethod
    def continue_multi_validation(self, ana_tag, user_id):
        pass


class Auto_Validation(Validation_Architecture):
    def __init__(self, opcclient, ana_tag, bottle_tag, user_id=None):
        self.taggs = self.select_taggs(ana_tag)  # tag들이 들어있는 row 데이터를 가져온다.
        self.bottle_tag = bottle_tag
        self.user_id = user_id
        self.parameter = self.select_analyzer_parameter(ana_tag, self.taggs[26])  # taggs[26] = network # purge_time, count가 구해진다.
        self.component = self.select_component_parameter(ana_tag, bottle_tag)  # component별로, wl, cl, 등이 구해진다.
        self.validation_taggs = self.select_validation_taggs(ana_tag)  # validation_tag가 구해진다.
        self.opcclient = opcclient
        self.alarm_tag = self.taggs[16]
        self.fault_tag = self.taggs[15]
        self.come_read_tag = self.taggs[12]
        self.index = self.taggs[25]
        self.count = self.parameter[6]

    def batch_singl_validation(self, ana_tag, user_id):
        come_read_init = 0
        cnt = 0
        alarm_no = 0
        fail_no = 0  # validation value가 upper, lower를 벗어났을 경우 변경되는 값.

        start_time = datetime.datetime.now()
        time.sleep((self.parameter[4]).seconds)  # purging

        validation_value = []
        validation_time = []

        while cnt != self.count:
            if ((self.geting_value(self.alarm_tag) == 1) or (self.geting_value(self.fault_tag) == 1)):  # alarm이나 fault신호가 있는지 확인,
                alarm_no = 1
            else:
                if self.single_slop_detector() == True:
                    if self.come_read_recognize() == 1:
                        if self.come_read_recognize() == come_read_init:
                            pass
                        elif self.come_read_recognize() != come_read_init:
                            print("recognized come read signal")

                            valid_value = self.geting_value(self.validation_taggs[0][0])
                            validation_value.append(valid_value)
                            validation_time.append(datetime.datetime.now())

                            if ((valid_value > self.component[0][4]) or (valid_value < self.component[0][5])):  # upper보다 크거나, lower보다 작으면 fail_no+=1
                                fail_no = 1
                            self.check_DCS(self.user_id, valid_value, self.validation_taggs[0][0], ana_tag)

                            come_read_init = 1
                            cnt += 1
                    elif self.come_read_recognize() == 0:  # 이 조건부는, 무한 반복루프 속에서 계속 저장하는 것을 방지하기 위함.
                        if come_read_init == 1:
                            come_read_init = 0
                        else:
                            pass
                else:
                    print("Value Unstable in Slop Detector")
        if alarm_no == 0:
            if fail_no == 0:
                statistic = Analysis_of_Variance(ana_tag, self.validation_taggs[0][0], "AUTO", validation_value,
                                                 start_time, validation_time, self.component, self.bottle_tag, user_id)
                RESULT = statistic.single_auto_statistics()
                return RESULT
            elif fail_no >= 1:
                db = withDB()
                for i in range(0, len(validation_value)):  # 측정한 값들을 모두 DB에 저장한다.
                    db.insertValidationData(ana_tag, self.validation_taggs[0][0], "AUTO", validation_value[i],
                                            start_time, validation_time[i], "FAIL", self.bottle_tag, user_id)
                db.close()
                RESULT = "FAIL"
                # 결과 DCS로 전송.
                return RESULT
        elif alarm_no >= 1:
            db = withDB()
            for i in range(0, len(validation_value)):  # 측정한 값들을 모두 DB에 저장한다.
                db.insertValidationData(ana_tag, self.validation_taggs[0][0], "AUTO", validation_value[i],
                                        start_time, validation_time[i], "ALARM", self.bottle_tag, user_id)  # Fail로 DB에 저장.
            db.close()
            RESULT = "ALARM"
            return RESULT

    def batch_multi_validation(self, ana_tag, user_id):
        come_read_init = 0
        cnt = 0
        alarm_no = 0
        fail_no = 0
        start_time = datetime.datetime.now()
        time.sleep((self.parameter[4]).seconds)  # purging

        validation_node = []
        for i in range(0, len(self.validation_taggs)):
            validation_node.append(self.validation_taggs[i][0])

        validation_value = []
        validation_time = []

        while cnt != self.count:
            if ((self.geting_value(self.alarm_tag) == 1) or (
                    self.geting_value(self.fault_tag) == 1)):  # alarm이나 fault신호가 있는지 확인,
                alarm_no = 1
            else:
                if self.multi_slop_detector() == True:
                    if self.come_read_recognize() == 1:
                        if self.come_read_recognize() == come_read_init:
                            pass
                        elif self.come_read_recognize() != come_read_init:
                            print("recognized come read signal")

                            for i in range(0, len(self.validation_taggs)):
                                valid_value = self.geting_value(self.validation_taggs[i][0])
                                validation_value.append(valid_value)
                            validation_time.append(datetime.datetime.now())  # validation value가 n개 들어가도, 해당 n개의 시간은 1개다.

                            for j in range(0, len(self.validation_taggs)):
                                upper = self.component[j][4]
                                lower = self.component[j][5]
                                if ((validation_value[-len(self.validation_taggs):][j] > upper) or (
                                        validation_value[-len(self.validation_taggs):][
                                            j] < lower)):  # upper보다 크거나, lower보다 작으면 fail_no+=1
                                    fail_no = 1
                            self.check_DCS(self.user_id, validation_value[-len(self.validation_taggs):], validation_node, ana_tag)

                            come_read_init = 1
                            cnt += 1
                    elif self.come_read_recognize() == 0:  # 이 조건부는, 무한 반복루프 속에서 계속 저장하는 것을 방지하기 위함.
                        if come_read_init == 1:
                            come_read_init = 0
                        else:
                            pass
                else:
                    print("Value Unstable in Slop Detector")
        if alarm_no == 0:
            if fail_no == 0:
                statistic = Analysis_of_Variance(ana_tag, validation_node, "AUTO", validation_value, start_time,
                                                 validation_time, self.component, self.bottle_tag, user_id)
                RESULT = statistic.multi_auto_statistics()
                return RESULT
            elif fail_no >= 1:
                db = withDB()
                count = 0
                for i in range(0, len(validation_value)):  # 측정한 값들을 모두 DB에 저장한다.
                    for k in range(0, len(
                            self.validation_taggs)):  # ('1630AI355A-VV',), ('1630AI355B-VV',), ('1630AI355C-VV',))
                        if i % len(self.validation_taggs) == k:
                            if i % len(self.validation_taggs) == (len(self.validation_taggs) - 1):
                                db.insertValidationData(ana_tag, self.validation_taggs[k][0], "AUTO", validation_value[i],
                                                        start_time, validation_time[count], "FAIL", self.bottle_tag, user_id)
                                count += 1
                            else:
                                db.insertValidationData(ana_tag, self.validation_taggs[k][0], "AUTO", validation_value[i],
                                                        start_time, validation_time[count], "FAIL", self.bottle_tag, user_id)
                db.close()
                RESULT = "FAIL"
                # 결과 DCS로 전송.
                return RESULT
        elif alarm_no >= 1:
            db = withDB()
            count = 0
            for i in range(0, len(validation_value)):  # 측정한 값들을 모두 DB에 저장한다.
                for k in range(0, len(
                        self.validation_taggs)):  # ('1630AI355A-VV',), ('1630AI355B-VV',), ('1630AI355C-VV',))
                    if i % len(self.validation_taggs) == k:
                        if i % len(self.validation_taggs) == (len(self.validation_taggs) - 1):
                            db.insertValidationData(ana_tag, self.validation_taggs[k][0], "AUTO", validation_value[i],
                                                    start_time, validation_time[count], "ALARM", self.bottle_tag, user_id)
                            count += 1
                        else:
                            db.insertValidationData(ana_tag, self.validation_taggs[k][0], "AUTO", validation_value[i],
                                                    start_time, validation_time[count], "ALARM", self.bottle_tag, user_id)
            db.close()
            RESULT = "ALARM"
            return RESULT  # validation 도중에 알람이 뜬 경우.

    def continue_singl_validation(self, ana_tag, user_id):
        cnt = 0
        alarm_no = 0
        fail_no = 0  # validation value가 upper, lower를 벗어났을 경우 변경되는 값.

        start_time = datetime.datetime.now()
        time.sleep((self.parameter[4]).seconds)  # purging

        print("after purge single continue")
        validation_value = []
        validation_time = []
        time_list = self.calculate_time_interval()

        while cnt != self.count:
            print(time_list, "시간리스트")
            if ((self.geting_value(self.alarm_tag) == 1) or (
                    self.geting_value(self.fault_tag) == 1)):  # alarm이나 fault신호가 있는지 확인,
                alarm_no = 1
            else:
                if self.single_slop_detector() == True:
                    valid_value = self.geting_value(self.validation_taggs[0][0])
                    if ((valid_value > self.component[0][4]) or (
                            valid_value < self.component[0][5])):  # upper보다 크거나, lower보다 작으면 fail_no+=1
                        fail_no = 1
                    self.check_DCS(self.user_id, valid_value, self.validation_taggs[0][0], ana_tag)

                    if time_list == []:
                        break
                    elif time_list[0] < datetime.datetime.now():
                        valid_value = self.geting_value(self.validation_taggs[0][0])
                        validation_value.append(valid_value)
                        validation_time.append(datetime.datetime.now())
                        self.check_DCS(self.user_id, valid_value, self.validation_taggs[0][0], ana_tag)

                        time_list.pop(0)
                        cnt += 1
                    else:
                        pass
                else:
                    print("Value Unstable in Slop Detector")
        if alarm_no == 0:
            if fail_no == 0:
                statistic = Analysis_of_Variance(ana_tag, self.validation_taggs[0][0], "AUTO", validation_value,
                                                 start_time, validation_time, self.component, self.bottle_tag, user_id)
                RESULT = statistic.single_auto_statistics()
                return RESULT
            elif fail_no >= 1:
                db = withDB()
                for i in range(0, len(validation_value)):  # 측정한 값들을 모두 DB에 저장한다.
                    db.insertValidationData(ana_tag, self.validation_taggs[0][0], "AUTO", validation_value[i],
                                            start_time, validation_time[i], "FAIL", self.bottle_tag, user_id)
                db.close()
                RESULT = "FAIL"
                # 결과 DCS로 전송.
                return RESULT
        elif alarm_no >= 1:
            db = withDB()
            for i in range(0, len(validation_value)):  # 측정한 값들을 모두 DB에 저장한다.
                db.insertValidationData(ana_tag, self.validation_taggs[0][0], "AUTO", validation_value[i],
                                        start_time, validation_time[i], "ALARM", self.bottle_tag, user_id)  # Fail로 DB에 저장.
            db.close()
            RESULT = "ALARM"
            return RESULT

    def continue_multi_validation(self, ana_tag, user_id):
        cnt = 0
        alarm_no = 0
        fail_no = 0
        start_time = datetime.datetime.now()
        time.sleep((self.parameter[4]).seconds)  # purging
        time_list = self.calculate_time_interval()

        validation_node = []
        for i in range(0, len(self.validation_taggs)):
            validation_node.append(self.validation_taggs[i][0])

        validation_value = []
        check_validation_value = []
        validation_time = []

        while cnt != self.count:
            if ((self.geting_value(self.alarm_tag) == 1) or (self.geting_value(self.fault_tag) == 1)):  # alarm이나 fault신호가 있는지 확인,
                alarm_no = 1
            else:
                if self.multi_slop_detector() == True:
                    for i in range(0, len(self.validation_taggs)):
                        valid_value = self.geting_value(self.validation_taggs[i][0])
                        validation_value.append(valid_value)

                    for j in range(0, len(self.validation_taggs)):
                        upper = self.component[j][4]
                        lower = self.component[j][5]
                        if ((validation_value[-len(self.validation_taggs):][j] > upper) or (
                                validation_value[-len(self.validation_taggs):][
                                    j] < lower)):  # upper보다 크거나, lower보다 작으면 fail_no+=1
                            fail_no = 1

                    self.check_DCS(self.user_id, validation_value[-len(self.validation_taggs):], validation_node, ana_tag)

                    if time_list[0] < datetime.datetime.now():
                        for i in range(0, len(self.validation_taggs)):
                            valid_value = self.geting_value(self.validation_taggs[i][0])
                            check_validation_value.append(valid_value)
                        validation_time.append(datetime.datetime.now())

                        self.check_DCS(self.user_id, check_validation_value[-len(self.validation_taggs):], validation_node, ana_tag)

                        time_list.pop(0)
                        cnt += 1
                    else:
                        pass
                else:
                    print("Value Unstable in Slop Detector")
        print(validation_time)
        if alarm_no == 0:
            if fail_no == 0:
                statistic = Analysis_of_Variance(ana_tag, validation_node, "AUTO", check_validation_value,
                                                 start_time, validation_time, self.component, self.bottle_tag, user_id)
                RESULT = statistic.multi_auto_statistics()
                return RESULT
            elif fail_no >= 1:
                db = withDB()
                count = 0
                for i in range(0, len(check_validation_value)):  # 측정한 값들을 모두 DB에 저장한다.
                    for k in range(0, len(
                            self.validation_taggs)):  # ('1630AI355A-VV',), ('1630AI355B-VV',), ('1630AI355C-VV',))
                        if i % len(self.validation_taggs) == k:
                            if i % len(self.validation_taggs) == (len(self.validation_taggs) - 1):
                                db.insertValidationData(ana_tag, self.validation_taggs[k][0], "AUTO", check_validation_value[i],
                                                        start_time, validation_time[count], "FAIL", self.bottle_tag, user_id)
                                count += 1
                            else:
                                db.insertValidationData(ana_tag, self.validation_taggs[k][0], "AUTO", check_validation_value[i],
                                                        start_time, validation_time[count], "FAIL", self.bottle_tag, user_id)
                db.close()
                RESULT = "FAIL"
                # 결과 DCS로 전송.
                return RESULT
        elif alarm_no >= 1:
            db = withDB()
            count = 0
            for i in range(0, len(check_validation_value)):  # 측정한 값들을 모두 DB에 저장한다.
                for k in range(0, len(
                        self.validation_taggs)):  # ('1630AI355A-VV',), ('1630AI355B-VV',), ('1630AI355C-VV',))
                    if i % len(self.validation_taggs) == k:
                        if i % len(self.validation_taggs) == (len(self.validation_taggs) - 1):
                            db.insertValidationData(ana_tag, self.validation_taggs[k][0], "AUTO", check_validation_value[i],
                                                    start_time, validation_time[count], "ALARM", self.bottle_tag, user_id)
                            count += 1
                        else:
                            db.insertValidationData(ana_tag, self.validation_taggs[k][0], "AUTO", check_validation_value[i],
                                                    start_time, validation_time[count], "ALARM", self.bottle_tag, user_id)
            db.close()
            RESULT = "ALARM"


class Semi_Auto_Validation(Validation_Architecture):
    def __init__(self, opcclient, ana_tag, bottle_tag, user_id=None):
        self.taggs = self.select_taggs(ana_tag)  # tag들이 들어있는 row 데이터를 가져온다.
        self.parameter = self.select_analyzer_parameter(ana_tag, self.taggs[
            26])  # taggs[26] = network # purge_time, count가 구해진다.
        self.component = self.select_component_parameter(ana_tag, bottle_tag)  # component별로, wl, cl, 등이 구해진다.
        self.user_id = user_id
        self.validation_taggs = self.select_validation_taggs(ana_tag)  # validation_tag가 구해진다.
        self.opcclient = opcclient
        self.alarm_tag = self.taggs[16]
        self.fault_tag = self.taggs[15]
        self.semi_auto_button_tag = self.taggs[27]
        self.come_read_tag = self.taggs[12]
        self.index = self.taggs[25]
        self.count = self.parameter[6]
        self.bottle_tag = bottle_tag

    def batch_singl_validation(self, ana_tag, user_id):
        come_read_init = 0
        semi_auto_init = 0
        cnt = 0
        alarm_no = 0
        fail_no = 0  # validation value가 upper, lower를 벗어났을 경우 변경되는 값.

        start_time = datetime.datetime.now()
        time.sleep((self.parameter[4]).seconds)  # purging

        print("Finish Purge SEMI_AUTO_VALIDAITON")
        validation_value = []
        validation_time = []

        valid_value = 0

        while cnt != self.count:
            if ((self.geting_value(self.alarm_tag) == 1) or (self.geting_value(self.fault_tag) == 1)):  # alarm이나 fault신호가 있는지 확인,
                alarm_no = 1
            else:
                if self.single_slop_detector() == True:
                    if self.semi_auto_recognize() == 1:
                        if self.semi_auto_recognize() == semi_auto_init:
                            pass
                        elif self.semi_auto_recognize() != semi_auto_init:
                            print("semiauto signal catch")
                            validation_value.append(valid_value)
                            validation_time.append(datetime.datetime.now())
                            print(valid_value)
                            if ((valid_value > self.component[0][4]) or (valid_value < self.component[0][5])):  # upper보다 크거나, lower보다 작으면 fail_no+=1
                                fail_no = 1

                            if self.user_id == "DCS":
                                pass
                            else:
                                to_client = dict()
                                to_client['message'] = valid_value
                                to_client['nodes'] = self.validation_taggs[0][0]
                                to_client['type'] = ana_tag
                                send(to_client, broadcast=True)

                            cnt += 1
                            semi_auto_init = 1
                            # print(cnt, self.count, "횟수 비교")
                    elif self.semi_auto_recognize() == 0:
                        if semi_auto_init == 1:
                            semi_auto_init = 0
                        else:
                            pass
                    if self.come_read_recognize() == 1:
                        if self.come_read_recognize() == come_read_init:
                            pass
                        elif self.come_read_recognize() != come_read_init:
                            valid_value = self.geting_value(self.validation_taggs[0][0])
                            print(valid_value, "<= validation value")
                            if self.user_id == "DCS":
                                pass
                            else:
                                to_client = dict()
                                to_client['message'] = valid_value
                                to_client['nodes'] = self.validation_taggs[0][0]
                                to_client['type'] = ana_tag
                                send(to_client, broadcast=True)
                            come_read_init = 1
                    elif self.come_read_recognize() == 0:  # 이 조건부는, 무한 반복루프 속에서 계속 저장하는 것을 방지하기 위함.
                        if come_read_init == 1:
                            come_read_init = 0
                        else:
                            pass
                else:
                    print("Value Unstable in Slop Detector")
        print("Before save DB")
        if alarm_no == 0:
            if fail_no == 0:
                statistic = Analysis_of_Variance(ana_tag,
                                                 self.validation_taggs[0][0],
                                                 "SEMI",
                                                 validation_value,
                                                 start_time,
                                                 validation_time,
                                                 self.component,
                                                 self.bottle_tag,
                                                 user_id)
                RESULT = statistic.single_auto_statistics()
                return RESULT
            elif fail_no >= 1:
                db = withDB()
                for i in range(0, len(validation_value)):  # 측정한 값들을 모두 DB에 저장한다.
                    db.insertValidationData(ana_tag,
                                            self.validation_taggs[0][0],
                                            "SEMI",
                                            validation_value[i],
                                            start_time,
                                            validation_time[i],
                                            "FAIL",
                                            self.bottle_tag,
                                            user_id)
                db.close()
                RESULT = "FAIL"
                # 결과 DCS로 전송.
                return RESULT
        elif alarm_no >= 1:
            db = withDB()
            for i in range(0, len(validation_value)):  # 측정한 값들을 모두 DB에 저장한다.
                db.insertValidationData(ana_tag,
                                        self.validation_taggs[0][0],
                                        "SEMI",
                                        validation_value[i],
                                        start_time,
                                        validation_time[i],
                                        "ALARM",
                                        self.bottle_tag,
                                        user_id)  # Fail로 DB에 저장.
            db.close()
            RESULT = "ALARM"
            return RESULT

    def batch_multi_validation(self, ana_tag, user_id):
        come_read_init = 0
        semi_auto_init = 0
        cnt = 0
        alarm_no = 0
        fail_no = 0
        start_time = datetime.datetime.now()
        time.sleep((self.parameter[4]).seconds)  # purging

        validation_node = []
        for i in range(0, len(self.validation_taggs)):
            validation_node.append(self.validation_taggs[i][0])

        validation_value = []
        check_validation_value = []
        validation_time = []

        while cnt != self.count:
            if ((self.geting_value(self.alarm_tag) == 1) or (
                    self.geting_value(self.fault_tag) == 1)):  # alarm이나 fault신호가 있는지 확인,
                alarm_no = 1
            else:
                if self.multi_slop_detector() == True:
                    if self.semi_auto_recognize() == 1:
                        if self.semi_auto_recognize() == semi_auto_init:
                            pass
                        elif self.semi_auto_recognize() != semi_auto_init:
                            print("recognized semi auto signal")
                            for i in range(0, len(validation_value)):
                                check_validation_value.append(validation_value[i])
                            validation_time.append(datetime.datetime.now())  # validation value가 n개 들어가도, 해당 n개의 시간은 1개다.

                            for j in range(0, len(self.validation_taggs)):
                                upper = self.component[j][4]
                                lower = self.component[j][5]
                                if ((check_validation_value[-len(self.validation_taggs):][j] > upper) or (check_validation_value[-len(self.validation_taggs):][j] < lower)):  # upper보다 크거나, lower보다 작으면 fail_no+=1
                                    fail_no = 1
                            if self.user_id == "DCS":
                                pass
                            else:
                                to_client = dict()
                                to_client['message'] = check_validation_value[-len(self.validation_taggs):]
                                print(check_validation_value[-len(self.validation_taggs):], "보내는 값 머 보내나.")
                                to_client['nodes'] = validation_node
                                to_client['type'] = ana_tag
                                send(to_client, broadcast=True)

                            cnt += 1
                            semi_auto_init = 1
                    elif self.semi_auto_recognize() == 0:  # 이 조건부는, 무한 반복루프 속에서 계속 저장하는 것을 방지하기 위함.
                        if semi_auto_init == 1:
                            semi_auto_init = 0
                        else:
                            pass
                    if self.come_read_recognize() == 1:
                        if self.come_read_recognize() == come_read_init:
                            pass
                        elif self.come_read_recognize() != come_read_init:
                            print("recognized come read signal")
                            validation_value = []
                            for i in range(0, len(self.validation_taggs)):
                                valid_value = self.geting_value(self.validation_taggs[i][0])
                                validation_value.append(valid_value)
                            for j in range(0, len(self.validation_taggs)):
                                upper = self.component[j][4]
                                lower = self.component[j][5]
                                if ((validation_value[-len(self.validation_taggs):][j] > upper) or (validation_value[-len(self.validation_taggs):][j] < lower)):  # upper보다 크거나, lower보다 작으면 fail_no+=1
                                    fail_no = 1
                            if self.user_id == "DCS":
                                pass
                            else:
                                to_client = dict()
                                to_client['message'] = validation_value[-len(self.validation_taggs):]
                                print(validation_value[-len(self.validation_taggs):], "<= validation_value")
                                to_client['nodes'] = validation_node
                                to_client['type'] = ana_tag
                                send(to_client, broadcast=True)

                            come_read_init = 1
                    elif self.come_read_recognize() == 0:  # 이 조건부는, 무한 반복루프 속에서 계속 저장하는 것을 방지하기 위함.
                        if come_read_init == 1:
                            come_read_init = 0
                        else:
                            pass
                else:
                    print("Value Unstable in Slop Detector")
        if alarm_no == 0:
            if fail_no == 0:
                statistic = Analysis_of_Variance(ana_tag, validation_node, "SEMI", check_validation_value, start_time,
                                                 validation_time, self.component, self.bottle_tag, user_id)
                RESULT = statistic.multi_auto_statistics()
                return RESULT
            elif fail_no >= 1:
                db = withDB()
                count = 0
                for i in range(0, len(check_validation_value)):  # 측정한 값들을 모두 DB에 저장한다.
                    for k in range(0, len(
                            self.validation_taggs)):  # ('1630AI355A-VV',), ('1630AI355B-VV',), ('1630AI355C-VV',))
                        if i % len(self.validation_taggs) == k:
                            if i % len(self.validation_taggs) == (len(self.validation_taggs) - 1):
                                db.insertValidationData(ana_tag,
                                                        self.validation_taggs[k][0],
                                                        "SEMI",
                                                        check_validation_value[i],
                                                        start_time,
                                                        validation_time[count],
                                                        "FAIL",
                                                        self.bottle_tag,
                                                        user_id)
                                count += 1
                            else:
                                db.insertValidationData(ana_tag,
                                                        self.validation_taggs[k][0],
                                                        "SEMI",
                                                        check_validation_value[i],
                                                        start_time,
                                                        validation_time[count],
                                                        "FAIL",
                                                        self.bottle_tag,
                                                        user_id)
                db.close()
                RESULT = "FAIL"
                # 결과 DCS로 전송.
                return RESULT
        elif alarm_no >= 1:
            db = withDB()
            count = 0
            for i in range(0, len(check_validation_value)):  # 측정한 값들을 모두 DB에 저장한다.
                for k in range(0, len(
                        self.validation_taggs)):  # ('1630AI355A-VV',), ('1630AI355B-VV',), ('1630AI355C-VV',))
                    if i % len(self.validation_taggs) == k:
                        if i % len(self.validation_taggs) == (len(self.validation_taggs) - 1):
                            db.insertValidationData(ana_tag, self.validation_taggs[k][0], "SEMI",
                                                    check_validation_value[i], start_time, validation_time[count],
                                                    "ALARM", self.bottle_tag, user_id)
                            count += 1
                        else:
                            db.insertValidationData(ana_tag,
                                                    self.validation_taggs[k][0],
                                                    "SEMI",
                                                    check_validation_value[i],
                                                    start_time,
                                                    validation_time[count],
                                                    "ALARM",
                                                    self.bottle_tag,
                                                    user_id)
            db.close()
            RESULT = "ALARM"
            return RESULT  # validation 도중에 알람이 뜬 경우.

    def continue_singl_validation(self, ana_tag, user_id):
        semi_auto_init = 0
        cnt = 0
        alarm_no = 0
        fail_no = 0  # validation value가 upper, lower를 벗어났을 경우 변경되는 값.

        start_time = datetime.datetime.now()
        time.sleep((self.parameter[4]).seconds)  # purging

        validation_value = []
        validation_time = []
        time_list = self.calculate_time_interval()

        while cnt != self.count:
            if ((self.geting_value(self.alarm_tag) == 1) or (
                    self.geting_value(self.fault_tag) == 1)):  # alarm이나 fault신호가 있는지 확인,
                alarm_no = 1
            else:
                time.sleep(0.5)
                if self.single_slop_detector() == True:
                    if self.semi_auto_recognize() == 1:
                        if self.semi_auto_recognize() == semi_auto_init:
                            pass
                        elif self.semi_auto_recognize() != semi_auto_init:
                            validation_value.append(valid_value)
                            validation_time.append(datetime.datetime.now())
                            print(valid_value, "<= save validation value")

                            if ((valid_value > self.component[0][4]) or (valid_value < self.component[0][5])):  # upper보다 크거나, lower보다 작으면 fail_no+=1
                                fail_no = 1
                            if self.user_id == "DCS":
                                pass
                            else:
                                to_client = dict()
                                to_client['message'] = valid_value
                                to_client['nodes'] = self.validation_taggs[0][0]
                                to_client['type'] = ana_tag
                                send(to_client, broadcast=True)

                            cnt += 1
                            semi_auto_init = 1
                    elif self.semi_auto_recognize() == 0:
                        if semi_auto_init == 1:
                            semi_auto_init = 0
                        else:
                            pass
                    valid_value = self.geting_value(self.validation_taggs[0][0])
                    if ((valid_value > self.component[0][4]) or (
                            valid_value < self.component[0][5])):  # upper보다 크거나, lower보다 작으면 fail_no+=1
                        fail_no = 1
                    if self.user_id == "DCS":
                        pass
                    else:
                        to_client = dict()
                        to_client['message'] = valid_value
                        to_client['nodes'] = self.validation_taggs[0][0]
                        to_client['type'] = ana_tag
                        send(to_client, broadcast=True)
                else:
                    print("Value Unstable in Slop Detector")
        if alarm_no == 0:
            if fail_no == 0:
                statistic = Analysis_of_Variance(ana_tag,
                                                 self.validation_taggs[0][0],
                                                 "SEMI",
                                                 validation_value,
                                                 start_time,
                                                 validation_time,
                                                 self.component,
                                                 self.bottle_tag,
                                                 user_id)
                RESULT = statistic.single_auto_statistics()
                return RESULT
            elif fail_no >= 1:
                db = withDB()
                for i in range(0, len(validation_value)):  # 측정한 값들을 모두 DB에 저장한다.
                    db.insertValidationData(ana_tag,
                                            self.validation_taggs[0][0],
                                            "SEMI",
                                            validation_value[i],
                                            start_time,
                                            validation_time[i],
                                            "FAIL",
                                            self.bottle_tag,
                                            user_id)
                db.close()
                RESULT = "FAIL"
                # 결과 DCS로 전송.
                return RESULT
        elif alarm_no >= 1:
            db = withDB()
            for i in range(0, len(validation_value)):  # 측정한 값들을 모두 DB에 저장한다.
                db.insertValidationData(ana_tag,
                                        self.validation_taggs[0][0],
                                        "SEMI",
                                        validation_value[i],
                                        start_time,
                                        validation_time[i],
                                        "ALARM",
                                        self.bottle_tag,
                                        user_id)  # Fail로 DB에 저장.
            db.close()
            RESULT = "ALARM"
            return RESULT

    def continue_multi_validation(self, ana_tag, user_id):
        semi_auto_init = 0
        cnt = 0
        alarm_no = 0
        fail_no = 0
        start_time = datetime.datetime.now()
        time.sleep((self.parameter[4]).seconds)  # purging
        time_list = self.calculate_time_interval()

        validation_node = []
        for i in range(0, len(self.validation_taggs)):
            validation_node.append(self.validation_taggs[i][0])

        validation_value = []
        check_validation_value = []
        validation_time = []

        while cnt != self.count:
            if ((self.geting_value(self.alarm_tag) == 1) or (self.geting_value(self.fault_tag) == 1)):  # alarm이나 fault신호가 있는지 확인,
                alarm_no = 1
            else:
                time.sleep(0.5)
                if self.multi_slop_detector() == True:
                    if self.semi_auto_recognize() == 1:
                        if self.semi_auto_recognize() == semi_auto_init:
                            pass
                        elif self.semi_auto_recognize() != semi_auto_init:
                            for i in range(0, len(validation_value)):
                                check_validation_value.append(validation_value[i])
                            validation_time.append(datetime.datetime.now())
                            if self.user_id == "DCS":
                                pass
                            else:
                                to_client = dict()
                                to_client['message'] = check_validation_value[-len(self.validation_taggs):]
                                to_client['nodes'] = validation_node
                                to_client['type'] = ana_tag
                                send(to_client, broadcast=True)

                            cnt += 1
                            semi_auto_init = 1
                    elif self.semi_auto_recognize() == 0:
                        if semi_auto_init == 1:
                            semi_auto_init = 0
                        else:
                            pass

                    validation_value = []
                    for i in range(0, len(self.validation_taggs)):
                        valid_value = self.geting_value(self.validation_taggs[i][0])
                        validation_value.append(valid_value)

                    for j in range(0, len(self.validation_taggs)):
                        upper = self.component[j][4]
                        lower = self.component[j][5]
                        if ((validation_value[-len(self.validation_taggs):][j] > upper) or (validation_value[-len(self.validation_taggs):][j] < lower)):  # upper보다 크거나, lower보다 작으면 fail_no+=1
                            fail_no = 1
                    if self.user_id == "DCS":
                        pass
                    else:
                        to_client = dict()
                        to_client['message'] = validation_value[-len(self.validation_taggs):]
                        to_client['nodes'] = validation_node
                        to_client['type'] = ana_tag
                        send(to_client, broadcast=True)
                else:
                    print("Value Unstable in Slop Detector")
        print(validation_time)
        if alarm_no == 0:
            if fail_no == 0:
                statistic = Analysis_of_Variance(ana_tag,
                                                 validation_node,
                                                 "SEMI",
                                                 check_validation_value,
                                                 start_time,
                                                 validation_time,
                                                 self.component,
                                                 self.bottle_tag,
                                                 user_id)
                RESULT = statistic.multi_auto_statistics()
                return RESULT
            elif fail_no >= 1:
                db = withDB()
                count = 0
                for i in range(0, len(check_validation_value)):  # 측정한 값들을 모두 DB에 저장한다.
                    for k in range(0, len(
                            self.validation_taggs)):  # ('1630AI355A-VV',), ('1630AI355B-VV',), ('1630AI355C-VV',))
                        if i % len(self.validation_taggs) == k:
                            if i % len(self.validation_taggs) == (len(self.validation_taggs) - 1):
                                db.insertValidationData(ana_tag,
                                                        self.validation_taggs[k][0],
                                                        "SEMI",
                                                        check_validation_value[i],
                                                        start_time,
                                                        validation_time[count],
                                                        "FAIL",
                                                        self.bottle_tag,
                                                        user_id)
                                count += 1
                            else:
                                db.insertValidationData(ana_tag,
                                                        self.validation_taggs[k][0],
                                                        "SEMI",
                                                        check_validation_value[i],
                                                        start_time,
                                                        validation_time[count],
                                                        "FAIL", self.bottle_tag,
                                                        user_id)
                db.close()
                RESULT = "FAIL"
                # 결과 DCS로 전송.
                return RESULT
        elif alarm_no >= 1:
            db = withDB()
            count = 0
            for i in range(0, len(check_validation_value)):  # 측정한 값들을 모두 DB에 저장한다.
                for k in range(0, len(
                        self.validation_taggs)):  # ('1630AI355A-VV',), ('1630AI355B-VV',), ('1630AI355C-VV',))
                    if i % len(self.validation_taggs) == k:
                        if i % len(self.validation_taggs) == (len(self.validation_taggs) - 1):
                            db.insertValidationData(ana_tag,
                                                    self.validation_taggs[k][0],
                                                    "SEMI",
                                                    check_validation_value[i],
                                                    start_time,
                                                    validation_time[count],
                                                    "ALARM",
                                                    self.bottle_tag,
                                                    user_id)
                            count += 1
                        else:
                            db.insertValidationData(ana_tag,
                                                    self.validation_taggs[k][0],
                                                    "SEMI",
                                                    check_validation_value[i],
                                                    start_time,
                                                    validation_time[count],
                                                    "ALARM",
                                                    self.bottle_tag,
                                                    user_id)
            db.close()
            RESULT = "ALARM"


class Manual_Validation(Validation_Architecture):
    def __init__(self, opcclient, ana_tag, bottle_tag, user_id=None):
        self.taggs = self.select_taggs(ana_tag)  # tag들이 들어있는 row 데이터를 가져온다.
        self.user_id = user_id
        self.parameter = self.select_analyzer_parameter(ana_tag, self.taggs[26])  # taggs[26] = network # purge_time, count가 구해진다.
        self.component = self.select_component_parameter(ana_tag, bottle_tag)  # component별로, wl, cl, 등이 구해진다.
        self.validation_taggs = self.select_validation_taggs(ana_tag)  # validation_tag가 구해진다.
        self.opcclient = opcclient
        self.alarm_tag = self.taggs[16]
        self.fault_tag = self.taggs[15]
        self.semi_auto_button_tag = self.taggs[27]
        self.come_read_tag = self.taggs[12]
        self.index = self.taggs[25]
        self.count = self.parameter[6]
        self.bottle_tag = bottle_tag

    def batch_singl_validation(self, ana_tag, user_id):
        cnt, semi_auto_init = 0, 0

        start_time = datetime.datetime.now()
        print("manual singl_batch start")
        while cnt == 0:
            if ((self.geting_value(self.alarm_tag) == 1) or (self.geting_value(self.fault_tag) == 1)):  # alarm이나 fault신호가 있는지 확인,
                alarm_no = 1
                return "ALARM"
            else:
                if self.semi_auto_recognize() == 1:
                    break
        print("manual singl_batch stop")
        db = withDB()
        datas = db.selectManualValidationData(ana_tag, start_time, user_id)
        db.close()
        print(datas)
        validation_value, validation_time = [],[]
        for i in range(0, len(datas)):
            validation_value.append(float(datas[i][5]))
            validation_time.append(datas[i][7])

        statistic = Analysis_of_Variance(ana_tag, self.validation_taggs[0][0], "MANUAL", validation_value, start_time,
                                         validation_time, self.component, self.bottle_tag, user_id)
        try:
            RESULT = statistic.single_auto_statistics()
            return RESULT
        except:
            self.dbmodule.insertExceptLogByTag(ana_tag, "batch_singl_opc_manual_validation")
            return "ERROR"

    def batch_multi_validation(self, ana_tag, user_id):
        cnt, semi_auto_init = 0, 0

        start_time = datetime.datetime.now()

        while cnt == 0:
            if ((self.geting_value(self.alarm_tag) == 1) or (self.geting_value(self.fault_tag) == 1)):  # alarm이나 fault신호가 있는지 확인,
                alarm_no = 1
                return "ALARM"
            else:
                if self.semi_auto_recognize() == 1:
                    break
        print("manual multi_batch stop")
        db = withDB()
        datas = db.selectManualValidationData(ana_tag, start_time, user_id)
        db.close()
        print(datas)
        validation_value, validation_time = [],[]
        for i in range(0, len(datas)):
            validation_value.append(float(datas[i][5]))
            if i%(self.count) == 0: # check_time만 담으려는 것.
                validation_time.append(datas[i][7])

        statistic = Analysis_of_Variance(ana_tag, self.validation_taggs[0][0], "MANUAL", validation_value, start_time,
                                         validation_time, self.component, self.bottle_tag, user_id)
        try:
            RESULT = statistic.multi_auto_statistics()
            return RESULT
        except:
            self.dbmodule.insertExceptLogByTag(ana_tag, "batch_multi_opc_manual_validation")
            return "ERROR"

    def continue_singl_validation(self, ana_tag, user_id):
        cnt, semi_auto_init = 0, 0

        start_time = datetime.datetime.now()

        while cnt == 0:
            if ((self.geting_value(self.alarm_tag) == 1) or (self.geting_value(self.fault_tag) == 1)):  # alarm이나 fault신호가 있는지 확인,
                alarm_no = 1
                return "ALARM"
            else:
                if self.semi_auto_recognize() == 1:
                    break
        print("manual singl_continue stop")
        db = withDB()
        datas = db.selectManualValidationData(ana_tag, start_time, user_id)
        db.close()
        print(datas)
        validation_value, validation_time = [],[]
        for i in range(0, len(datas)):
            validation_value.append(float(datas[i][5]))
            validation_time.append(datas[i][7])

        statistic = Analysis_of_Variance(ana_tag, self.validation_taggs[0][0], "MANUAL", validation_value, start_time,
                                         validation_time, self.component, self.bottle_tag, user_id)
        try:
            RESULT = statistic.single_auto_statistics()
            return RESULT
        except:
            self.dbmodule.insertExceptLogByTag(ana_tag, "continue_singl_opc_manual_validation")
            return "ERROR"

    def continue_multi_validation(self, ana_tag, user_id):
        cnt, semi_auto_init = 0, 0

        start_time = datetime.datetime.now()

        while cnt == 0:
            if ((self.geting_value(self.alarm_tag) == 1) or (self.geting_value(self.fault_tag) == 1)):  # alarm이나 fault신호가 있는지 확인,
                alarm_no = 1
                return "ALARM"
            else:
                if self.semi_auto_recognize() == 1:
                    break
        print("manual multi_continue stop")
        db = withDB()
        datas = db.selectManualValidationData(ana_tag, start_time, user_id)
        db.close()
        print(datas)
        validation_value, validation_time = [],[]
        for i in range(0, len(datas)):
            validation_value.append(float(datas[i][5]))
            if i%(self.count) == 0: # check_time만 담으려는 것.
                validation_time.append(datas[i][7])

        statistic = Analysis_of_Variance(ana_tag, self.validation_taggs[0][0], "MANUAL", validation_value, start_time,
                                         validation_time, self.component, self.bottle_tag, user_id)
        try:
            RESULT = statistic.multi_auto_statistics()
            return RESULT
        except:
            self.dbmodule.insertExceptLogByTag(ana_tag, "continue_multi_opc_manual_validation")
            return "ERROR"