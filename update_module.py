from lxml import etree
import pymysql
import datetime
import time

from db_sql_module import *
from reform_module import *


class update: # DB의 내용을 찾아서 갱신하는것과 관련된 기능만 모여있다.
    def __init__(self, conn):
        self.conn = conn

    def update_validation_result(self, start_time, result, user_id):
        cursor = self.conn.cursor()
        sql = updateValidationResult()
        cursor.execute(sql, (result, start_time)) # 우선 user_id 막아놓음.
        self.conn.commit()
