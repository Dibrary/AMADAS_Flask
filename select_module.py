from lxml import etree
import pymysql
import datetime
import time

from db_sql_module import *
from reform_module import *


class select: # DB의 내용을 찾아서 가져오는 것과 관련된 기능만 모여있다.
    def __init__(self, conn):
        self.conn = conn

    def analyzer_count(self):
        cursor = self.conn.cursor()
        sql = analyzerCount()
        cursor.execute(sql, ())
        values = cursor.fetchall()
        return tuple_to_list(values)

    def house_count(self):
        cursor = self.conn.cursor()
        sql = houseCount()
        cursor.execute(sql, ())
        values = cursor.fetchall()
        return tuple_to_list(values)

    def analyzer_network(self, ana_tag):
        cursor = self.conn.cursor()
        try:
            sql = analyzerNetwork()
            cursor.execute(sql, (ana_tag))
            values = cursor.fetchall()
            return tuple_to_list(values)
        except:
            return "OPC"

    def analyzer_tag(self, ana_tag, network):
        cursor = self.conn.cursor()
        try:
            sql = analyzerTag()
            cursor.execute(sql, (ana_tag, network))
            values = cursor.fetchall()
            return tuple_to_list(values)
        except:
            return None

    def analyzer_tag_by_tag(self, ana_tag):
        cursor = self.conn.cursor()
        sql = analyzerTagByTag()
        cursor.execute(sql, (ana_tag))
        values = cursor.fetchall()
        return values[0]

    def analyzer_tag_by_tag2(self, ana_tag):
        cursor = self.conn.cursor()
        sql = analyzerTagByTag2()
        cursor.execute(sql, (ana_tag, "MODBUS"))
        values = cursor.fetchall()
        return values[0]

    def bottle_valve_by_tag(self, ana_tag, bottle_tag, network):
        cursor = self.conn.cursor()
        sql = bottleValveByTag()
        cursor.execute(sql, (ana_tag, bottle_tag, network))
        values = cursor.fetchall()
        return values[0][0]

    def bottle_expire_by_tag(self, ana_tag, bottle_tag):
        cursor = self.conn.cursor()
        try:
            sql = bottleExpire()
            cursor.execute(sql, (ana_tag, bottle_tag))
            values = cursor.fetchall()
            return tuple_to_list(values)
        except:
            return datetime.datetime.now()

    def tag_no_by_tag(self, event_type, object_tag, event_tag):
        sql = ''
        cursor = self.conn.cursor()
        if event_type == "MAINT":
            sql = tagnoBymaintTag()
        elif event_type == "ALARM":
            sql = tagnoByalarmTag()
        elif event_type == "FAULT":
            sql = tagnoByfaultTag()
        elif event_type == "BREAK":
            sql = tagnoBybreakTag()
        elif event_type == "VALID":
            sql = tagnoByvalidTag()
        elif event_type == "CALIB":
            sql = tagnoBycalibTag()
        cursor.execute(sql, (object_tag, event_tag))
        values = cursor.fetchall()
        return values

    def tag_no_by_ana_tag(self, ana_tag, network):
        cursor = self.conn.cursor()
        sql = analyzerTag()
        cursor.execute(sql, (ana_tag, network))
        network_value = cursor.fetchall()

        sql2 = tagNoByAnaTag()
        cursor.execute(sql2, (ana_tag, network_value[0][26]))
        tag_no = cursor.fetchall()
        return tag_no # 반환 형은 ((2,),) 이런 꼴.

    def first_schedule(self):
        cursor = self.conn.cursor()
        sql = firstSchedule()
        cursor.execute(sql, ())
        values = cursor.fetchall()
        return tuple_to_list(values)

    def house_index_and_network(self, house_tag):
        cursor = self.conn.cursor()
        try:
            sql = houseIndexAndNetwork()
            cursor.execute(sql, (house_tag))
            values = cursor.fetchall()
            return values[0]
        except:
            return None

    def all_analyzer_tag_by_house_index(self, index):
        cursor = self.conn.cursor()
        sql = allAnalyzerTagByHouseIndex()
        cursor.execute(sql, (index))
        values = cursor.fetchall()
        return values

    def in_valid_tag_by_index(self, index):
        cursor = self.conn.cursor()
        sql = inValidTagByIndex()
        cursor.execute(sql, (index[0][0]))
        values = cursor.fetchall()
        return values[0][0]

    def analyzer_type_by_tag(self, ana_tag):
        cursor = self.conn.cursor()
        sql = analyzerTypeByTag()
        cursor.execute(sql, (ana_tag))
        values = cursor.fetchall()
        return tuple_to_list(values)

    def analyzer_node_by_tag(self, ana_tag):
        cursor = self.conn.cursor()
        sql = analyzerNodeByTag()
        cursor.execute(sql, (ana_tag, ana_tag))
        values = cursor.fetchall()
        return values

    def analyzer_tag_and_LIMS(self):
        cursor = self.conn.cursor()
        sql = analyzerTagAndLIMS()
        cursor.execute(sql, ())
        values = cursor.fetchall()
        return values

    def process_tag_by_tag(self, ana_tag):
        cursor = self.conn.cursor()
        sql = processTagByTag()
        cursor.execute(sql, (ana_tag))
        values = cursor.fetchall()
        return values

    def analyzer_process_index(self, ana_tag):
        cursor = self.conn.cursor()
        sql = analyzerProcessIndex()
        cursor.execute(sql, (ana_tag))
        values = cursor.fetchall()
        return values

    def AnalyzerEventTag(self):
        cursor = self.conn.cursor()
        sql = analyzerEventTag()
        cursor.execute(sql, ())
        values = cursor.fetchall()
        return values

    def analyzer_no_by_tag(self, ana_tag):
        cursor = self.conn.cursor()
        sql = analyzerNoByTag()
        cursor.execute(sql, (ana_tag))
        values = cursor.fetchall()
        return values[0]

    def analyzer_parameter_by_tag(self, ana_tag, network):
        cursor = self.conn.cursor()
        sql = analyzerParameterByTag()
        cursor.execute(sql, (ana_tag, network))
        values = cursor.fetchall()
        return values[0]

    def component_parameter_by_tag(self, ana_tag, bottle_tag):
        cursor = self.conn.cursor()
        sql = componentParameterByTag()
        cursor.execute(sql, (ana_tag, bottle_tag))
        values = cursor.fetchall()
        return values

    def component_parameter_by_tag2(self, ana_tag, bottle_tag):
        cursor = self.conn.cursor()
        sql = componentParameterByTag2()
        cursor.execute(sql, (ana_tag, bottle_tag, "MODBUS"))
        values = cursor.fetchall()
        return values

    def validation_tag_by_tag(self, ana_tag):
        cursor = self.conn.cursor()
        sql = validationTagByTag()
        cursor.execute(sql, (ana_tag))
        values = cursor.fetchall()
        return values

    def validation_tag_by_tag2(self, ana_tag):
        cursor = self.conn.cursor()
        sql = validationTagByTag2()
        cursor.execute(sql, (ana_tag, "MODBUS"))
        values = cursor.fetchall()
        return values

    def validation_tag_index_by_tag(self, ana_tag, validation_tag, network):
        cursor = self.conn.cursor()
        sql = validationTagIndexByTag()
        cursor.execute(sql, (ana_tag, network, validation_tag))
        values = cursor.fetchall()
        return values

    def bottle_index_by_tag(self, bottle_tag):
        cursor = self.conn.cursor()
        sql = bottleIndexByTag()
        cursor.execute(sql, (bottle_tag))
        values = cursor.fetchall()
        return values[0]

    def housetag_by_analyzertag(self, ana_tag):
        cursor = self.conn.cursor()
        sql = houseTagByAnalyzerTag()
        cursor.execute(sql, (ana_tag))
        values = cursor.fetchall()
        return values[0][0]

    def data_for_report(self, start_dt, end_dt, div, ana_tag=None):
        cursor = self.conn.cursor()
        sql = ''
        if ana_tag != None:
            if div == "Validation":
                sql = validation_data_for_report()
            elif div == "Trend":
                sql = trend_data_for_report()
            elif div == "Maintenance":
                sql = maintenance_data_for_report()
            elif div == "Alarm":
                sql = alarm_data_for_report()
            elif div == "Breakdown":
                sql = breakdown_data_for_kpi()
            elif div == "Check":
                sql = check_data_for_kpi()
            cursor.execute(sql, (ana_tag, start_dt, end_dt))
        if div == "Whole":
            sql = whole_data_for_report()
            cursor.execute(sql, (start_dt, end_dt))

        values = cursor.fetchall()
        if values == ():
            return None
        else:
            return list(values)

    def ptmr_data_by_tag(self, ana_tag):
        cursor = self.conn.cursor()
        sql = ptmrDataByTag()
        cursor.execute(sql, (ana_tag))
        values = cursor.fetchall()
        return values

    def multi_ptmr_data_by_tag(self, ana_tag, bottle_tag):
        cursor = self.conn.cursor()
        sql = multiPtmrDataByTag()
        cursor.execute(sql, (ana_tag, bottle_tag))
        values = cursor.fetchall()
        return values

    def process_by_between_date(self, ana_tag, process_tag, start_dt, end_dt):
        cursor = self.conn.cursor()
        sql = processByBetweenDate()
        cursor.execute(sql, (ana_tag, process_tag, start_dt, end_dt))
        values = cursor.fetchall()
        return values

    def analyzer_tag_index_by_tag(self, ana_tag):
        cursor = self.conn.cursor()
        sql = analyzerTagIndexByTag()
        cursor.execute(sql, (ana_tag))
        values = cursor.fetchall()
        return values[0]

    def analyzer_tag_index_modbus_by_tag(self, ana_tag, network):
        cursor = self.conn.cursor()
        sql = analyzerTagIndexModbusByTag()
        cursor.execute(sql, (ana_tag, network))
        values = cursor.fetchall()
        return values[0]

    def process_tag_index_by_process_tag(self, ana_tag_index, process_tag):
        cursor = self.conn.cursor()
        sql = processTagIndexByProcessTag()
        cursor.execute(sql, (ana_tag_index, process_tag))
        values = cursor.fetchall()
        return values[0]

    def manual_validation_data(self, ana_tag_index, start_time, user_id):
        cursor = self.conn.cursor()
        sql = manualValidationData()
        cursor.execute(sql, (start_time, ana_tag_index, user_id))
        values = cursor.fetchall()
        return values

    def select_all_analyzer_tag(self):
        cursor = self.conn.cursor()
        sql = selectAllAnalyzer()
        cursor.execute(sql, ())
        values = cursor.fetchall()
        return values

    def select_process_tag_to_infinit_by_tag(self, ana_tag, network):
        cursor = self.conn.cursor()
        sql = analyzerNodeByProcessTag()
        cursor.execute(sql, (ana_tag, ana_tag, network))
        values = cursor.fetchall()
        return values

    def default_valve_by_tag(self, ana_tag):
        cursor = self.conn.cursor()
        sql = defaultValveByTag()
        cursor.execute(sql, (ana_tag))
        values = cursor.fetchall() # 여기 값이 (('PULSE',),) 이렇게 나온다.
        return values[0][0]

    def default_bottle_tag_by_tag(self, ana_tag):
        cursor = self.conn.cursor()
        sql = defaultBottleTagByTag()
        cursor.execute(sql, (ana_tag))
        values = cursor.fetchall() # 여기 값이 (('태그',),) 이렇게 나온다.
        return values[0][0]

    def default_validation_type_by_tag(self, ana_tag):
        cursor = self.conn.cursor()
        sql = defaultValidationTypeByTag()
        cursor.execute(sql, (ana_tag))
        values = cursor.fetchall() # 여기 값이 (('AUTO',),) 이렇게 나온다.
        return values[0][0]

    def event_datas_by_tag(self, ana_tag, start_dt, end_dt, div):
        cursor = self.conn.cursor()
        if div == "Alarm":
            sql = eventAlarmDatasByTag()
        elif div == "Maintenance":
            sql = eventMaintDatasByTag()
        cursor.execute(sql, (ana_tag, start_dt, end_dt))
        values = cursor.fetchall()
        print(values, "출력")
        return values