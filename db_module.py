from lxml import etree
import pymysql
import datetime
import time

from select_module import select
from insert_module import insert
from update_module import update
from delete_module import delete

def db_module_chooser(div, conn):
    result = None
    if div == "SELECT":
        result = select(conn)
    elif div == "INSERT":
        result = insert(conn)
    elif div == "DELETE":
        result = delete(conn)
    return result


class withDB:
    def __init__(self):
        root = (etree.parse("opc_modbus_db_ip.xml")).getroot()
        for j in root.iter("address"):
            self.version = int(j.findtext("version"))
        for i in root.iter("dbserver"):
            ip = i.findtext("ip")
            user = i.findtext("user")
            port = i.findtext("port")
            password = i.findtext("password")
            db = i.findtext("db")
        conn = pymysql.connect(host=ip, port=int(port), user=user, password=password, db=db, charset='utf8') # xml파일에 설정된 정보를 가지고 MySQL에 접속한다.
        self.conn = conn

    def close(self):
        return self.conn.close() # DB접속을 끊는다.

    def analyzerCount(self):
        self.select = select(self.conn)
        return self.select.analyzer_count()

    def houseCount(self):
        self.select = select(self.conn)
        return self.select.house_count()

    def selectAnalyzerNetwork(self, ana_tag):
        self.select = select(self.conn)
        return self.select.analyzer_network(ana_tag)

    def selectAnalyzerTag(self, ana_tag, network):
        self.select = select(self.conn)
        return self.select.analyzer_tag(ana_tag, network)

    def selectBottleExpireByTag(self, ana_tag, bottle_tag):
        self.select = select(self.conn)
        return self.select.bottle_expire_by_tag(ana_tag, bottle_tag)

    def insertEventStartLog(self, object_tag, event_type, event_tag, user_id=None):
        self.insert = insert(self.conn)
        self.select = select(self.conn)
        index = self.select.tag_no_by_tag(event_type, object_tag, event_tag)
        self.insert.insert_event_start_log(index[0][0], object_tag, event_type, event_tag, user_id)

##############################################################################################################
    def insertValidationEventStartLog(self, ana_tag, type, start_time, user_id): # user_id로 들어어오는 것 auto / semiauto는 validation type이 들어온다.
        self.insert = insert(self.conn)
        self.select = select(self.conn)
        network = None
        if self.version == 1: network = 'OPC'
        else:                 network = 'MODBUS'
        ana_tag_index = self.select.tag_no_by_ana_tag(ana_tag, network)
        in_valid_tag = self.select.in_valid_tag_by_index(ana_tag_index)
        self.insert.insert_valid_status_log(ana_tag_index, in_valid_tag, type, start_time, "START", user_id)


    def insertValidationEventStopLog(self, ana_tag, type, user_id):
        now = datetime.datetime.now() # 이 함수가 불러지는 그 시간을 적음.
        self.insert = insert(self.conn)
        self.select = select(self.conn)
        network = None
        if self.version == 1: network = 'OPC'
        else:                 network = 'MODBUS'

        ana_tag_index = self.select.tag_no_by_ana_tag(ana_tag, network)
        in_valid_tag = self.select.in_valid_tag_by_index(ana_tag_index)
        self.insert.insert_valid_status_log(ana_tag_index, in_valid_tag, type, now, "STOP", user_id)

##############################################################################################################
    # 위 메서드는 manual일 때 못 쓰는 문제가 있다;;




    def insertEventStopLog(self, object_tag, event_type, event_tag, user_id=None):
        self.insert = insert(self.conn)
        self.select = select(self.conn)
        index = self.select.tag_no_by_tag(event_type, object_tag, event_tag)
        self.insert.insert_event_stop_log(index, object_tag, event_type, event_tag, user_id)

    def selectFirstScheduler(self):
        self.select = select(self.conn)
        return self.select.first_schedule()

    def deleteFirstScheduler(self):
        self.delete = delete(self.conn)
        self.delete.first_schedule()

    def selectHouseIndexAndNetwork(self, house_tag):
        self.select = select(self.conn)
        values = self.select.house_index_and_network(house_tag)
        return values

    def selectAllAnalyzerTagByHouseIndex(self, index):
        self.select = select(self.conn)
        taggs = self.select.all_analyzer_tag_by_house_index(index)
        return taggs

    def selectAnalyzerTypeByTag(self, ana_tag):
        self.select = select(self.conn)
        analyzer_type = self.select.analyzer_type_by_tag(ana_tag)
        return analyzer_type

    def selectAnalyzerNodeByTag(self, ana_tag):
        self.select = select(self.conn)
        analyzer_node = self.select.analyzer_node_by_tag(ana_tag)
        return analyzer_node

    def selectAnalyzerTagAndLIMS(self):
        self.select = select(self.conn)
        result = self.select.analyzer_tag_and_LIMS()
        return result

    def selectProcessTagByTag(self, ana_tag):
        self.select = select(self.conn)
        process_node = self.select.process_tag_by_tag(ana_tag)
        return process_node

    def save_LIMS_data(self, ana_tag, result):
        self.select = select(self.conn)
        self.insert = insert(self.conn)
        index = self.select.analyzer_process_index(ana_tag)
        self.insert.save_LIMS_data(index, result)

    def selectAnalyzerEventTag(self):
        self.select = select(self.conn)
        result = self.select.AnalyzerEventTag()
        return result

    def selectAnalyzerTagByTag(self, ana_tag):
        self.select = select(self.conn)
        result = self.select.analyzer_tag_by_tag(ana_tag)
        return result

    def selectAnalyzerTagByTag2(self, ana_tag):
        self.select = select(self.conn)
        result = self.select.analyzer_tag_by_tag2(ana_tag)
        return result

    def selectBottleValve(self, ana_tag, bottle_tag, network):
        self.select = select(self.conn)
        result = self.select.bottle_valve_by_tag(ana_tag, bottle_tag, network)
        return result

    def selectAnalyzerParameterByTag(self, ana_tag, network):
        self.select = select(self.conn)
        result = self.select.analyzer_parameter_by_tag(ana_tag, network)
        return result

    def selectComponentParameterByTag(self, ana_tag, bottle_tag):
        self.select = select(self.conn)
        result = self.select.component_parameter_by_tag(ana_tag, bottle_tag)
        return result

    def selectComponentParameterByTag2(self, ana_tag, bottle_tag):
        self.select = select(self.conn)
        result = self.select.component_parameter_by_tag2(ana_tag, bottle_tag)
        return result

    def selectValidationTagByTag(self, ana_tag):
        self.select = select(self.conn)
        result = self.select.validation_tag_by_tag(ana_tag)
        return result

    def selectValidationTagByTag2(self, ana_tag):
        self.select = select(self.conn)
        result = self.select.validation_tag_by_tag2(ana_tag)
        return result

    def insertValidationData(self, ana_tag, validation_tag, validation_type, validation_value, start_time, check_time,
                             result, bottle_tag, user_id=None):
        self.select = select(self.conn)
        network = None
        if self.version == 2 or self.version == 3 or self.version == 4:
            network = "MODBUS"
        elif self.version == 1:
            network = "OPC"
        print(ana_tag, validation_tag, network, "DB들어가는 거")
        index = self.select.validation_tag_index_by_tag(ana_tag, validation_tag, network)
        bottle_index = self.select.bottle_index_by_tag(bottle_tag)
        in_valid_tag = self.select.in_valid_tag_by_index(index)
        self.insert = insert(self.conn)
        if user_id == None:
            user_id = "AUTO"
        self.insert.validation_data(index[0], bottle_index, validation_type, in_valid_tag, validation_value, start_time, check_time, result, user_id)

    def selectHousetagByAnalyzertag(self, ana_tag):
        self.select = select(self.conn)
        result = self.select.housetag_by_analyzertag(ana_tag)
        return result

    def selectAnalyzerNoByTag(self, ana_tag):
        self.select = select(self.conn)
        result = self.select.analyzer_no_by_tag(ana_tag)
        return result

    def dataForReport(self, start_dt, end_dt, div, ana_tag=None):
        self.select = select(self.conn)
        result = self.select.data_for_report(start_dt, end_dt, div, ana_tag)
        return result

    def selectPtmrDataByTag(self, ana_tag):
        self.select = select(self.conn)
        result = self.select.ptmr_data_by_tag(ana_tag)
        return result

    def selectMultiPtmrDataByTag(self, ana_tag, bottle_tag):
        self.select = select(self.conn)
        result = self.select.multi_ptmr_data_by_tag(ana_tag, bottle_tag)
        return result

    def selectProcessByBetweenDate(self, ana_tag, process_tag, start_dt, end_dt):
        self.select = select(self.conn)
        result = self.select.process_by_between_date(ana_tag, process_tag, start_dt, end_dt)
        return result

    def insertLimsData(self, ana_tag, process_tag, process_value, start_dt, end_dt, result):
        self.select = select(self.conn)
        ana_tag_index = self.select.analyzer_tag_index_by_tag(ana_tag)
        process_tag_index = self.select.process_tag_index_by_process_tag(ana_tag_index, process_tag)
        self.insert = insert(self.conn)
        self.insert.lims_data(ana_tag_index[0], process_tag_index[0], process_value, start_dt, end_dt, result)

    def selectManualValidationData(self, ana_tag, start_time, user_id):
        self.select = select(self.conn)
        ana_tag_index = self.select.analyzer_tag_index_by_tag(ana_tag)
        result = self.select.manual_validation_data(ana_tag_index, start_time, user_id)
        return result

    def updateValidationManualData(self, start_time, result, user_id):
        self.update = update(self.conn)
        self.update.update_validation_result(start_time, result, user_id)

    def selectAllAnalyzer(self):
        self.select = select(self.conn)
        result= self.select.select_all_analyzer_tag()
        return result

    def selectProcessTagToInfinitByTag(self, ana_tag, network):
        self.select = select(self.conn)
        result = self.select.select_process_tag_to_infinit_by_tag(ana_tag, network)
        return result

    def insertProcessValueRealtime(self, ana_tag, process_tag, value, network):
        self.select = select(self.conn)
        ana_tag_index = self.select.analyzer_tag_index_modbus_by_tag(ana_tag, network)
        process_tag_index = self.select.process_tag_index_by_process_tag(ana_tag_index, process_tag)
        self.insert = insert(self.conn)
        self.insert.save_realtime_process_value(ana_tag_index[0], process_tag_index[0], value)

    def selectDefaultValveByTag(self, ana_tag):
        self.select = select(self.conn)
        result = self.select.default_valve_by_tag(ana_tag)
        return result

    def selectDefaultBottleTagByTag(self, ana_tag):
        self.select = select(self.conn)
        result = self.select.default_bottle_tag_by_tag(ana_tag)
        return result

    def selectDefaultValidationTypeByTag(self, ana_tag):
        self.select = select(self.conn)
        result = self.select.default_validation_type_by_tag(ana_tag)
        return result

    def selectEventDatasByTag(self, ana_tag, start_dt, end_dt, div):
        self.select = select(self.conn)
        result = self.select.event_datas_by_tag(ana_tag, start_dt, end_dt, div)
        return result

    def insertExceptLogByTag(self, object_tag, method_name):
        self.insert = insert(self.conn)
        self.insert.except_log_by_tag(object_tag, method_name)