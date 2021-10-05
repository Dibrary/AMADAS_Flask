from decimal import *

from db_module import *
from statistical_module import *


class lims_module:
    def __init__(self, ana_tag, process_tag, start_dt, end_dt, lims_value):
        self.ana_tag = ana_tag
        self.process_tag = process_tag
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.lims_value = lims_value

    def select_process_data(self):
        db = withDB()
        try:
            print(self.start_dt, self.end_dt, "여기 process값 꺼내오는 곳.")
            datas = db.selectProcessByBetweenDate(self.ana_tag, self.process_tag, self.start_dt, self.end_dt)
            db.close()
            return datas
        except:
            db.insertExceptLogByTag(self.ana_tag, "lims_select_process_data")
            db.close()
            return None

    def select_component_value(self):
        pass  # component를 찾아서 wl범위를 계산 부분에 주려 했으나, wl은 validation에만 존재한다.

    def compare_process_value(self):
        process_values = self.select_process_data()  # (('1630AI155A', Decimal('4.40')), ('1630AI155A', Decimal('7.30')))
        try:
            ls = LIMS_statistics(self.ana_tag, self.process_tag, self.start_dt, self.end_dt, self.lims_value, process_values)
            db = withDB()
            result = ls.single_lims_compare()
        except:
            db.insertExceptLogByTag(self.ana_tag, "lims_manual_compare")
            db.close()
            return "ERROR"
        print(self.ana_tag, self.process_tag, self.lims_value, self.start_dt, self.end_dt, float(result), "머 나오나 보자.")
        db.insertLimsData(self.ana_tag, self.process_tag, self.lims_value, self.start_dt, self.end_dt, float(result))
        db.close()
        return result