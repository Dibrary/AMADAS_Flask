import pymysql
import datetime
import time

from db_sql_module import *
from reform_module import *


class insert:# DB에 내용을 삽입하는 것과 관련된 기능만 모여있다.
    def __init__(self, conn):
        self.conn = conn

    def close(self):
        return self.conn.close()

    def insert_event_start_log(self, index, object_tag, event_type, event_tag, user_id=None):
        now = datetime.datetime.now()
        cursor = self.conn.cursor()
        sql = insertEventLog()
        if user_id == None:
            user_id = 'AUTO'
        else:
            pass
        cursor.execute(sql, (index, event_tag, event_type, now, "START", user_id))
        self.conn.commit()

    def insert_event_stop_log(self, index, object_tag, event_type, event_tag, user_id=None):
        now = datetime.datetime.now()
        cursor = self.conn.cursor()
        sql = insertEventLog()
        if user_id == None:
            user_id = 'AUTO'
        else:
            pass
        cursor.execute(sql, (index, event_tag, event_type, now, "STOP", user_id))
        self.conn.commit()

    def save_LIMS_data(self, index, result):
        print("SAVE LIMS BUTTON DATA ")
        now = datetime.datetime.now()
        cursor = self.conn.cursor()
        sql = insertLIMSData()
        for i in range(0, len(result)):
            cursor.execute(sql, (index[i][0], index[i][1], result[i], now, now))
        self.conn.commit()

    def validation_data(self, index, bottle_index, validation_type, validation_value,
                        start_time, check_time, result, user_id):
        cursor = self.conn.cursor()
        sql = insertValidationData()
        cursor.execute(sql, (index[0], bottle_index, index[1], validation_type,
                             validation_value, start_time, check_time, result, user_id))
        self.conn.commit()

    def lims_data(self, ana_tag_index, process_tag_index, process_value, start_dt, end_dt, result):
        cursor = self.conn.cursor()
        sql = insertLimsData()
        cursor.execute(sql, (ana_tag_index, process_tag_index, process_value, start_dt, end_dt, result))
        self.conn.commit()

    def save_realtime_process_value(self, ana_tag_index, process_tag_index, value):
        cursor = self.conn.cursor()
        sql = insertProcessDataRealtime()
        cursor.execute(sql, (process_tag_index, ana_tag_index, value, datetime.datetime.now()))
        self.conn.commit()

    def except_log_by_tag(self, object_tag, method_name):
        cursor = self.conn.cursor()
        sql = insertExceptLogByTag()
        cursor.execute(sql, (object_tag, method_name, datetime.datetime.now()))
        self.conn.commit()