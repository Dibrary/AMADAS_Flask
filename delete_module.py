from lxml import etree
import pymysql
import datetime
import time

from db_sql_module import *
from reform_module import *


class delete: # DB의 내용을 삭제하는 것과 관련된 기능만 모여있다.
    def __init__(self, conn):
        self.conn = conn

    def first_schedule(self):
        cursor = self.conn.cursor()
        sql = deleteFirstSchedule()
        cursor.execute(sql, ())
        self.conn.commit()
