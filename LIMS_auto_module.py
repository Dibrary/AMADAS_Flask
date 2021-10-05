
from db_module import *

class Auto_LIMS_Data_Save:
    def __init__(self):
        root = (etree.parse("opc_modbus_db_ip.xml")).getroot()
        for i in root.iter("limsserver"):
            ip = i.findtext("ip")
            user = i.findtext("user")
            port = i.findtext("port")
            password = i.findtext("password")
            db = i.findtext("db")
        conn = pymysql.connect(host=ip, port=int(port), user=user, password=password, db=db, charset='utf8')
        self.conn = conn

    def read_and_save_lims(self): # LIMS DB가 따로 있으면, 해당 ip를 토대로, DB의 내용을 가져오는 코드 작성 예정.
        pass